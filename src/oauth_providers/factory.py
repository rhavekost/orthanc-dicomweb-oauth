"""OAuth provider factory."""
from typing import Any, Dict, Type

from src.oauth_providers.aws import AWSProvider
from src.oauth_providers.azure import AzureOAuthProvider
from src.oauth_providers.base import OAuthConfig, OAuthProvider
from src.oauth_providers.generic import GenericOAuth2Provider
from src.oauth_providers.google import GoogleProvider
from src.oauth_providers.managed_identity import AzureManagedIdentityProvider


class OAuthProviderFactory:
    """
    Factory for creating OAuth provider instances.

    Supports automatic provider detection or explicit specification.
    """

    # Registry of provider types
    _providers: Dict[str, Type[OAuthProvider]] = {
        "generic": GenericOAuth2Provider,
        "azure": AzureOAuthProvider,
        "google": GoogleProvider,
        "aws": AWSProvider,
        "azuremanagedidentity": AzureManagedIdentityProvider,
        # Add more providers here as implemented:
        # "keycloak": KeycloakOAuthProvider,
    }

    @classmethod
    def create(cls, provider_type: str, config: Dict[str, Any]) -> OAuthProvider:
        """
        Create an OAuth provider instance.

        Args:
            provider_type: Provider type (e.g., 'azure', 'google', 'generic')
            config: Provider configuration dict

        Returns:
            OAuthProvider instance

        Raises:
            ValueError: If provider type is unknown
        """
        if provider_type not in cls._providers:
            raise ValueError(
                f"Unknown provider type: {provider_type}. "
                f"Supported: {list(cls._providers.keys())}"
            )

        # Provider-specific initialization
        provider_class = cls._providers[provider_type]

        # Managed identity uses raw config dict, not OAuthConfig
        if provider_type == "azuremanagedidentity":
            return provider_class(config)  # type: ignore[arg-type]

        # Convert dict config to OAuthConfig for other providers
        oauth_config = OAuthConfig(
            token_endpoint=config["TokenEndpoint"],
            client_id=config["ClientId"],
            client_secret=config["ClientSecret"],
            scope=config.get("Scope", ""),
            verify_ssl=config.get("VerifySSL", True),
        )

        if provider_type == "azure":
            tenant_id = config.get("TenantId", "common")
            return provider_class(oauth_config, tenant_id)
        else:
            return provider_class(oauth_config)

    @classmethod
    def register_provider(
        cls, provider_type: str, provider_class: Type[OAuthProvider]
    ) -> None:
        """Register a custom provider type."""
        cls._providers[provider_type] = provider_class

    @classmethod
    def auto_detect(cls, config: Dict[str, Any]) -> str:
        """
        Auto-detect provider type from configuration.

        Args:
            config: Provider configuration dict

        Returns:
            Detected provider type
        """
        token_endpoint = config.get("TokenEndpoint", "")

        # Azure detection
        if "login.microsoftonline.com" in token_endpoint:
            return "azure"

        # Google detection
        if "oauth2.googleapis.com" in token_endpoint:
            return "google"

        # AWS detection
        if "amazonaws.com" in token_endpoint or "aws" in token_endpoint.lower():
            return "aws"

        # Keycloak detection
        if "/auth/realms/" in token_endpoint:
            return "keycloak"

        # Default to generic
        return "generic"
