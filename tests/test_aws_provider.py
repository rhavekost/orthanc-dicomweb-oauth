"""Tests for AWS HealthImaging OAuth provider."""

from src.oauth_providers.aws import AWSProvider


def test_aws_provider_initialization() -> None:
    """Test AWSProvider initialization."""
    config = {
        "Region": "us-west-2",
        "ClientId": "AKIAIOSFODNN7EXAMPLE",
        "ClientSecret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "UseInstanceProfile": False,
        "TokenEndpoint": "https://sts.amazonaws.com/",
    }

    provider = AWSProvider(config)

    assert provider.provider_name == "aws"
    assert provider.region == "us-west-2"
    assert provider.config.client_id == "AKIAIOSFODNN7EXAMPLE"


def test_aws_provider_default_region() -> None:
    """Test AWSProvider uses default region."""
    config = {
        "ClientId": "test-key",
        "ClientSecret": "test-secret",
        "TokenEndpoint": "https://sts.amazonaws.com/",
    }

    provider = AWSProvider(config)
    assert provider.region == "us-west-2"
