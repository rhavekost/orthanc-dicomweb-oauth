"""Configuration parser for DICOMweb OAuth plugin."""
import os
import re
from typing import Dict, Any, Optional


class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass


class ConfigParser:
    """Parse and validate plugin configuration from Orthanc JSON config."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize parser with Orthanc configuration.

        Args:
            config: Full Orthanc configuration dict
        """
        self.config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate that required configuration structure exists."""
        if "DicomWebOAuth" not in self.config:
            raise ConfigError("Missing 'DicomWebOAuth' section in configuration")

        if "Servers" not in self.config["DicomWebOAuth"]:
            raise ConfigError("Missing 'Servers' section in DicomWebOAuth configuration")

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
        processed = {}
        for key, value in config.items():
            if isinstance(value, str):
                processed[key] = self._substitute_env_vars(value)
            else:
                processed[key] = value
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
        pattern = r'\$\{([^}]+)\}'

        def replace_var(match):
            var_name = match.group(1)
            if var_name not in os.environ:
                raise ConfigError(
                    f"Environment variable '{var_name}' referenced in config but not set"
                )
            return os.environ[var_name]

        return re.sub(pattern, replace_var, value)
