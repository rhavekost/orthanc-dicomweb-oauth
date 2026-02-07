"""OAuth2 token acquisition and caching for DICOMweb connections."""
import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, cast

import requests

from src.error_codes import ErrorCode, NetworkError, TokenAcquisitionError
from src.metrics import MetricsCollector
from src.oauth_providers.base import OAuthProvider
from src.oauth_providers.factory import OAuthProviderFactory
from src.resilience.circuit_breaker import CircuitBreaker
from src.resilience.retry_strategy import (
    ExponentialBackoff,
    FixedBackoff,
    LinearBackoff,
    RetryConfig,
    RetryStrategy,
)
from src.secrets_manager import SecretsManager
from src.structured_logger import structured_logger

logger = logging.getLogger(__name__)

# Explicitly export public API
__all__ = [
    "TokenManager",
    "TokenAcquisitionError",
    "MAX_TOKEN_ACQUISITION_RETRIES",
    "INITIAL_RETRY_DELAY_SECONDS",
    "TOKEN_REQUEST_TIMEOUT_SECONDS",
    "DEFAULT_TOKEN_EXPIRY_SECONDS",
    "DEFAULT_REFRESH_BUFFER_SECONDS",
]

# Token acquisition configuration constants
MAX_TOKEN_ACQUISITION_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 1
TOKEN_REQUEST_TIMEOUT_SECONDS = 30
DEFAULT_TOKEN_EXPIRY_SECONDS = 3600
DEFAULT_REFRESH_BUFFER_SECONDS = 300


class TokenManager:
    """Manages OAuth2 token acquisition, caching, and refresh for a DICOMweb server."""

    def __init__(self, server_name: str, config: Dict[str, Any]) -> None:
        """
        Initialize token manager for a DICOMweb server.

        Args:
            server_name: Name of the server (for logging)
            config: Server configuration containing TokenEndpoint, ClientId, etc.
        """
        self.server_name = server_name
        self.config = config
        self._validate_config()

        # Initialize secrets manager for encryption
        self._secrets_manager = SecretsManager()

        # Token cache (encrypted)
        self._encrypted_cached_token: Optional[bytes] = None
        self._token_expiry: Optional[datetime] = None
        self._lock = threading.Lock()

        # Configuration
        self.token_endpoint = config["TokenEndpoint"]
        self.client_id = config["ClientId"]

        # Encrypt client secret in memory
        self._encrypted_client_secret = self._secrets_manager.encrypt_secret(
            config["ClientSecret"]
        )

        self.scope = config.get("Scope", "")
        self.refresh_buffer_seconds = config.get(
            "TokenRefreshBufferSeconds", DEFAULT_REFRESH_BUFFER_SECONDS
        )
        self.verify_ssl = config.get("VerifySSL", True)

        # Create OAuth provider
        provider_type = config.get("ProviderType", "auto")
        if provider_type == "auto":
            provider_type = OAuthProviderFactory.auto_detect(config)

        self.provider: OAuthProvider = OAuthProviderFactory.create(
            provider_type=provider_type,
            config={
                **config,
                "ClientSecret": self._get_client_secret(),  # Decrypt only when needed
            },
        )

        # Initialize resilience features
        self._circuit_breaker = self._create_circuit_breaker(config)
        self._retry_config = self._create_retry_config(config)

        structured_logger.info(
            "Token manager initialized with encrypted secrets",
            server=server_name,
            provider=self.provider.provider_name,
        )

    def _get_client_secret(self) -> str:
        """
        Decrypt and return client secret.

        Returns:
            Decrypted client secret
        """
        return self._secrets_manager.decrypt_secret(self._encrypted_client_secret)

    def _set_cached_token(self, token: str) -> None:
        """
        Encrypt and cache access token.

        Args:
            token: Access token to cache
        """
        self._encrypted_cached_token = self._secrets_manager.encrypt_secret(token)

    def _get_cached_token(self) -> Optional[str]:
        """
        Decrypt and return cached token.

        Returns:
            Decrypted token or None if no token cached
        """
        if self._encrypted_cached_token is None:
            return None
        return self._secrets_manager.decrypt_secret(self._encrypted_cached_token)

    def _validate_config(self) -> None:
        """Validate that required configuration keys are present."""
        required_keys = ["TokenEndpoint", "ClientId", "ClientSecret"]
        missing_keys = [key for key in required_keys if key not in self.config]

        if missing_keys:
            raise ValueError(
                f"Server '{self.server_name}' missing required config keys: "
                f"{missing_keys}"
            )

    def _create_circuit_breaker(
        self, config: Dict[str, Any]
    ) -> Optional[CircuitBreaker]:
        """Create circuit breaker from config."""
        resilience_config = config.get("ResilienceConfig", {})

        if not resilience_config.get("CircuitBreakerEnabled", False):
            return None

        return CircuitBreaker(
            failure_threshold=resilience_config.get(
                "CircuitBreakerFailureThreshold", 5
            ),
            timeout=resilience_config.get("CircuitBreakerTimeout", 60.0),
            exception_filter=lambda e: isinstance(
                e, (requests.Timeout, requests.ConnectionError, TokenAcquisitionError)
            ),
        )

    def _create_retry_config(self, config: Dict[str, Any]) -> Optional[RetryConfig]:
        """Create retry config from config."""
        resilience_config = config.get("ResilienceConfig", {})

        max_attempts = resilience_config.get("RetryMaxAttempts")
        if max_attempts is None:
            return None

        # Create strategy based on config
        strategy_type = resilience_config.get("RetryStrategy", "exponential")
        initial_delay = resilience_config.get("RetryInitialDelay", 1.0)

        strategy: RetryStrategy
        if strategy_type == "fixed":
            strategy = FixedBackoff(delay=initial_delay)
        elif strategy_type == "linear":
            increment = resilience_config.get("RetryIncrement", 1.0)
            strategy = LinearBackoff(initial_delay=initial_delay, increment=increment)
        else:  # exponential
            multiplier = resilience_config.get("RetryMultiplier", 2.0)
            max_delay = resilience_config.get("RetryMaxDelay")
            strategy = ExponentialBackoff(
                initial_delay=initial_delay,
                multiplier=multiplier,
                max_delay=max_delay,
            )

        return RetryConfig(
            max_attempts=max_attempts,
            strategy=strategy,
            should_retry=lambda e: not isinstance(e, TokenAcquisitionError),
            on_retry=lambda attempt, exc: structured_logger.warning(
                "Token acquisition retry",
                server=self.server_name,
                attempt=attempt + 1,
                max_attempts=max_attempts,
                error=str(exc),
            ),
        )

    def get_token(self) -> str:
        """
        Get a valid OAuth2 access token, acquiring or refreshing as needed.

        Returns:
            Valid access token string

        Raises:
            TokenAcquisitionError: If token acquisition fails
        """
        metrics = MetricsCollector.get_instance()

        with self._lock:
            # Check if we have a valid cached token
            if self._is_token_valid():
                # Record cache hit
                metrics.record_cache_hit(self.server_name)

                structured_logger.debug(
                    "Using cached token",
                    server=self.server_name,
                    operation="get_token",
                    cached=True,
                )
                logger.debug(f"Using cached token for server '{self.server_name}'")

                cached_token = self._get_cached_token()
                assert cached_token is not None  # Validated by _is_token_valid
                return cached_token

            # Record cache miss
            metrics.record_cache_miss(self.server_name)

            # Need to acquire a new token
            structured_logger.info(
                "Acquiring new token",
                server=self.server_name,
                operation="get_token",
                cached=False,
            )
            logger.info(f"Acquiring new token for server '{self.server_name}'")
            return self._acquire_token()

    def _is_token_valid(self) -> bool:
        """Check if cached token exists and is not expiring soon."""
        if self._encrypted_cached_token is None or self._token_expiry is None:
            return False

        # Token is valid if it won't expire within the buffer window
        now = datetime.now(timezone.utc)
        buffer = timedelta(seconds=self.refresh_buffer_seconds)
        return now + buffer < self._token_expiry

    def _acquire_token(self) -> str:
        """
        Acquire a new OAuth2 token using provider with retry logic.

        Returns:
            Access token string

        Raises:
            TokenAcquisitionError: If acquisition fails after all retries
        """
        metrics = MetricsCollector.get_instance()
        start_time = time.time()

        structured_logger.info(
            "Starting token acquisition",
            server=self.server_name,
            operation="acquire_token",
            provider=self.provider.provider_name,
            endpoint=self.token_endpoint,
        )

        def acquire_operation() -> str:
            """Core token acquisition logic."""
            # Use configured retry or fall back to legacy retry
            if self._retry_config:
                return self._acquire_with_retry_config()
            else:
                return self._acquire_with_legacy_retry()

        try:
            # Apply circuit breaker if enabled
            if self._circuit_breaker:
                result = cast(str, self._circuit_breaker.call(acquire_operation))
            else:
                result = acquire_operation()

            # Record successful acquisition
            duration = time.time() - start_time
            metrics.record_token_acquisition(
                self.server_name, success=True, duration=duration
            )

            return result
        except Exception:
            # Record failed acquisition
            duration = time.time() - start_time
            metrics.record_token_acquisition(
                self.server_name, success=False, duration=duration
            )
            raise

    def _acquire_with_retry_config(self) -> str:
        """Acquire token using configured retry strategy."""
        assert self._retry_config is not None

        def attempt_acquire() -> str:
            oauth_token = self.provider.acquire_token()

            # Cache encrypted token
            self._set_cached_token(oauth_token.access_token)
            self._token_expiry = datetime.now(timezone.utc) + timedelta(
                seconds=oauth_token.expires_in
            )

            # Validate token if provider supports it
            if not self.provider.validate_token(oauth_token.access_token):
                raise TokenAcquisitionError(
                    ErrorCode.TOKEN_VALIDATION_FAILED,
                    "Token validation failed",
                    details={
                        "server": self.server_name,
                        "provider": self.provider.provider_name,
                    },
                )

            structured_logger.info(
                "Token acquired and validated",
                server=self.server_name,
                operation="acquire_token",
                provider=self.provider.provider_name,
                expires_in_seconds=oauth_token.expires_in,
            )
            logger.info(
                f"Token acquired for server '{self.server_name}', "
                f"expires in {oauth_token.expires_in} seconds"
            )

            cached_token = self._get_cached_token()
            assert cached_token is not None
            return cached_token

        try:
            return cast(str, self._retry_config.execute(attempt_acquire))
        except (TokenAcquisitionError, NetworkError):
            # Re-raise structured errors as-is (they already have error codes)
            raise
        except Exception as e:
            error_msg = f"Failed to acquire token for server '{self.server_name}': {e}"
            structured_logger.error(
                "Token acquisition failed",
                server=self.server_name,
                operation="acquire_token",
                provider=self.provider.provider_name,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            logger.error(error_msg)
            raise TokenAcquisitionError(
                ErrorCode.TOKEN_ACQUISITION_FAILED,
                error_msg,
                details={
                    "server": self.server_name,
                    "provider": self.provider.provider_name,
                    "original_error": str(e),
                },
            ) from e

    def _acquire_with_legacy_retry(self) -> str:
        """Legacy token acquisition with hardcoded exponential backoff."""
        max_retries = MAX_TOKEN_ACQUISITION_RETRIES
        retry_delay = INITIAL_RETRY_DELAY_SECONDS

        for attempt in range(max_retries):
            try:
                # Use provider to acquire token
                oauth_token = self.provider.acquire_token()

                # Cache encrypted token
                self._set_cached_token(oauth_token.access_token)
                self._token_expiry = datetime.now(timezone.utc) + timedelta(
                    seconds=oauth_token.expires_in
                )

                # Validate token if provider supports it
                if not self.provider.validate_token(oauth_token.access_token):
                    raise TokenAcquisitionError(
                        ErrorCode.TOKEN_VALIDATION_FAILED,
                        "Token validation failed",
                        details={
                            "server": self.server_name,
                            "provider": self.provider.provider_name,
                            "attempt": attempt + 1,
                        },
                    )

                structured_logger.info(
                    "Token acquired and validated",
                    server=self.server_name,
                    operation="acquire_token",
                    provider=self.provider.provider_name,
                    expires_in_seconds=oauth_token.expires_in,
                    attempt=attempt + 1,
                )
                logger.info(
                    f"Token acquired for server '{self.server_name}', "
                    f"expires in {oauth_token.expires_in} seconds"
                )

                cached_token = self._get_cached_token()
                assert cached_token is not None
                return cached_token

            except (requests.Timeout, requests.ConnectionError, NetworkError) as e:
                if attempt < max_retries - 1:
                    structured_logger.warning(
                        "Token acquisition retry",
                        server=self.server_name,
                        operation="acquire_token",
                        provider=self.provider.provider_name,
                        attempt=attempt + 1,
                        max_attempts=max_retries,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        retry_delay_seconds=retry_delay,
                    )
                    logger.warning(
                        f"Token acquisition attempt {attempt + 1} failed for "
                        f"server '{self.server_name}': {e}. "
                        f"Retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    error_msg = (
                        f"Failed to acquire token for server '{self.server_name}' "
                        f"after {max_retries} attempts: {e}"
                    )
                    structured_logger.error(
                        "Token acquisition failed",
                        server=self.server_name,
                        operation="acquire_token",
                        provider=self.provider.provider_name,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        max_attempts=max_retries,
                    )
                    logger.error(error_msg)
                    raise TokenAcquisitionError(
                        ErrorCode.TOKEN_ACQUISITION_FAILED,
                        error_msg,
                        details={
                            "server": self.server_name,
                            "provider": self.provider.provider_name,
                            "attempts": max_retries,
                            "error_type": type(e).__name__,
                        },
                    ) from e

            except (TokenAcquisitionError, NetworkError):
                # Provider-specific errors with error codes, re-raise immediately
                raise

            except Exception as e:
                # Unexpected errors
                error_msg = (
                    f"Failed to acquire token for server '{self.server_name}': {e}"
                )
                structured_logger.error(
                    "Token acquisition failed",
                    server=self.server_name,
                    operation="acquire_token",
                    provider=self.provider.provider_name,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    retryable=False,
                )
                logger.error(error_msg)
                raise TokenAcquisitionError(
                    ErrorCode.TOKEN_ACQUISITION_FAILED,
                    error_msg,
                    details={
                        "server": self.server_name,
                        "provider": self.provider.provider_name,
                        "error_type": type(e).__name__,
                    },
                ) from e

        # This should never be reached, but satisfies mypy
        raise TokenAcquisitionError(
            ErrorCode.TOKEN_ACQUISITION_FAILED,
            f"Failed to acquire token for server '{self.server_name}'",
            details={"server": self.server_name},
        )
