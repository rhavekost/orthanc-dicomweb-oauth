"""Tests for environment-specific configuration."""
import json
from pathlib import Path


def test_staging_config_exists():
    """Staging configuration file should exist."""
    staging_config = Path("docker/orthanc-staging.json")
    assert staging_config.exists(), "Staging config must exist"


def test_staging_config_valid_json():
    """Staging config should be valid JSON."""
    with open("docker/orthanc-staging.json") as f:
        config = json.load(f)
    assert isinstance(config, dict)


def test_staging_config_has_environment_marker():
    """Staging config should clearly identify environment."""
    with open("docker/orthanc-staging.json") as f:
        config = json.load(f)
    assert "Name" in config
    assert "staging" in config["Name"].lower() or "Staging" in config["Name"]


def test_staging_has_authentication_enabled():
    """Staging must have authentication enabled for security."""
    with open("docker/orthanc-staging.json") as f:
        config = json.load(f)
    assert (
        config.get("AuthenticationEnabled") is True
    ), "Staging environment must have authentication enabled"


def test_staging_has_ssl_verification():
    """Staging should have SSL verification enabled."""
    with open("docker/orthanc-staging.json") as f:
        config = json.load(f)

    oauth_config = config.get("DicomWebOAuth", {})
    servers = oauth_config.get("Servers", {})

    for server_name, server_config in servers.items():
        verify_ssl = server_config.get("VerifySSL", True)
        assert (
            verify_ssl is True
        ), f"Staging server '{server_name}' must have SSL verification enabled"


def test_dev_config_has_security_warning():
    """Development config should have clear security warning."""
    with open("docker/orthanc.json") as f:
        config = json.load(f)

    name = config.get("Name", "")
    assert (
        "Development" in name or "DEV" in name
    ), "Development config should clearly identify environment in Name"
