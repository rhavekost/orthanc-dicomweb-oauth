"""Tests for configuration versioning and migration."""
from src.config_migration import detect_config_version, migrate_config


def test_detect_v1_config() -> None:
    """Test detection of v1 configuration."""
    config_v1 = {
        "DicomWebOAuth": {
            "Servers": {
                "server1": {
                    "Url": "https://pacs.example.com/dicomweb",
                    "TokenEndpoint": "https://login.example.com/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                }
            }
        }
    }

    version = detect_config_version(config_v1)
    assert version == "1.0"


def test_detect_v2_config() -> None:
    """Test detection of v2 configuration with explicit version."""
    config_v2 = {
        "ConfigVersion": "2.0",
        "DicomWebOAuth": {
            "Servers": {
                "server1": {
                    "Url": "https://pacs.example.com/dicomweb",
                    "TokenEndpoint": "https://login.example.com/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "ProviderType": "azure",
                }
            }
        },
    }

    version = detect_config_version(config_v2)
    assert version == "2.0"


def test_migrate_v1_to_v2() -> None:
    """Test migration from v1 to v2 configuration."""
    config_v1 = {
        "DicomWebOAuth": {
            "Servers": {
                "server1": {
                    "Url": "https://pacs.example.com/dicomweb",
                    "TokenEndpoint": "https://login.example.com/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                }
            }
        }
    }

    migrated = migrate_config(config_v1)

    # Should have version field
    assert "ConfigVersion" in migrated
    assert migrated["ConfigVersion"] == "2.0"

    # Server config should be preserved
    assert "server1" in migrated["DicomWebOAuth"]["Servers"]

    # Should have default provider type
    server = migrated["DicomWebOAuth"]["Servers"]["server1"]
    assert "ProviderType" in server
    assert server["ProviderType"] == "auto"


def test_migrate_already_v2() -> None:
    """Test that v2 config is not modified."""
    config_v2 = {
        "ConfigVersion": "2.0",
        "DicomWebOAuth": {
            "Servers": {
                "server1": {
                    "Url": "https://pacs.example.com/dicomweb",
                    "TokenEndpoint": "https://login.example.com/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "ProviderType": "azure",
                }
            }
        },
    }

    migrated = migrate_config(config_v2)

    # Should be unchanged
    assert migrated == config_v2
