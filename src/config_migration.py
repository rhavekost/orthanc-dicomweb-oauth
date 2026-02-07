"""Configuration versioning and migration."""
import copy
import logging
from typing import Any, Dict, cast

logger = logging.getLogger(__name__)

# Current configuration version
CURRENT_VERSION = "2.0"


def detect_config_version(config: Dict[str, Any]) -> str:
    """
    Detect configuration version.

    Args:
        config: Configuration dictionary

    Returns:
        Version string (e.g., "1.0", "2.0")
    """
    # Explicit version field (v2+)
    if "ConfigVersion" in config:
        return cast(str, config["ConfigVersion"])

    # No version field = v1.0
    return "1.0"


def migrate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate configuration to current version.

    Args:
        config: Configuration dictionary (any version)

    Returns:
        Migrated configuration at current version
    """
    current_version = detect_config_version(config)

    # Already at current version
    if current_version == CURRENT_VERSION:
        return config

    # Make a deep copy to avoid mutating original
    migrated = copy.deepcopy(config)

    # Apply migrations in sequence
    if current_version == "1.0":
        migrated = _migrate_v1_to_v2(migrated)
        logger.info("Migrated configuration from v1.0 to v2.0")

    return migrated


def _migrate_v1_to_v2(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate v1.0 configuration to v2.0.

    Changes in v2.0:
    - Add ConfigVersion field
    - Add ProviderType field to servers (default: "auto")
    - Add TokenRefreshBufferSeconds default

    Args:
        config: v1.0 configuration

    Returns:
        v2.0 configuration
    """
    # Add version field
    config["ConfigVersion"] = "2.0"

    # Add defaults to each server
    if "DicomWebOAuth" in config and "Servers" in config["DicomWebOAuth"]:
        for server_name, server_config in config["DicomWebOAuth"]["Servers"].items():
            # Add ProviderType if missing
            if "ProviderType" not in server_config:
                server_config["ProviderType"] = "auto"

            # Add TokenRefreshBufferSeconds if missing
            if "TokenRefreshBufferSeconds" not in server_config:
                server_config["TokenRefreshBufferSeconds"] = 300

    return config
