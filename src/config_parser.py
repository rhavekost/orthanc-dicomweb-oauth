"""Configuration parser for DICOMweb OAuth plugin."""
import os
import re
from typing import Any, Dict, Match

from src.config_migration import migrate_config as migrate_config_version
from src.config_schema import validate_config
from src.error_codes import ConfigurationError, ErrorCode


class ConfigError(Exception):
    """Raised when configuration is invalid (deprecated - use ConfigurationError)."""

    pass


class ConfigParser:
    """Parse and validate plugin configuration from Orthanc JSON config."""

    def __init__(self, config: Dict[str, Any], validate_schema: bool = True):
        """
        Initialize parser with Orthanc configuration.

        Args:
            config: Full Orthanc configuration dict
            validate_schema: Whether to validate against JSON Schema (default True)
        """
        # Migrate config to current version
        self.config = migrate_config_version(config)
        self._validate_config(validate_schema=validate_schema)

    def _validate_config(self, validate_schema: bool = True) -> None:
        """
        Validate that required configuration structure exists.

        Args:
            validate_schema: Whether to validate against JSON Schema
        """
        if "DicomWebOAuth" not in self.config:
            raise ConfigurationError(
                ErrorCode.CONFIG_MISSING_KEY,
                "Missing 'DicomWebOAuth' section in configuration",
                details={"missing_key": "DicomWebOAuth"},
            )

        if "Servers" not in self.config["DicomWebOAuth"]:
            raise ConfigurationError(
                ErrorCode.CONFIG_MISSING_KEY,
                "Missing 'Servers' section in DicomWebOAuth configuration",
                details={"missing_key": "Servers", "parent": "DicomWebOAuth"},
            )

        # Validate against JSON Schema if enabled
        if validate_schema:
            try:
                validate_config(self.config)
            except Exception as e:
                raise ConfigurationError(
                    ErrorCode.CONFIG_INVALID_VALUE,
                    f"Configuration validation failed: {e}",
                    details={"validation_error": str(e)},
                ) from e

    def get_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all configured DICOMweb servers with OAuth settings.

        Returns:
            Dictionary mapping server names to their configurations
        """
        servers = self.config["DicomWebOAuth"]["Servers"]
        processed_servers = {}

        for name, server_config in servers.items():
            processed_servers[name] = self._process_server_config(server_config)

        return processed_servers

    def _process_server_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single server configuration, applying env var substitution.

        Args:
            config: Raw server configuration

        Returns:
            Processed configuration with environment variables expanded
        """
        processed: Dict[str, Any] = {}
        for key, value in config.items():
            if isinstance(value, str):
                processed[key] = self._substitute_env_vars(value)
            else:
                processed[key] = value

        # SSL/TLS Verification (defaults to True for security)
        if "VerifySSL" not in processed:
            processed["VerifySSL"] = True

        return processed

    def _substitute_env_vars(self, value: str) -> str:
        """
        Replace ${VAR_NAME} patterns with environment variable values.

        Args:
            value: String that may contain ${VAR_NAME} patterns

        Returns:
            String with environment variables expanded

        Raises:
            ConfigError: If a referenced environment variable is not set
        """
        pattern = r"\$\{([^}]+)\}"

        def replace_var(match: Match[str]) -> str:
            var_name = match.group(1)
            if var_name not in os.environ:
                raise ConfigurationError(
                    ErrorCode.CONFIG_ENV_VAR_MISSING,
                    (
                        f"Environment variable '{var_name}' referenced in "
                        "config but not set"
                    ),
                    details={"variable_name": var_name},
                )
            return os.environ[var_name]

        return re.sub(pattern, replace_var, value)
