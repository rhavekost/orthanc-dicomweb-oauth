"""Tests for AWS HealthImaging OAuth provider."""

from unittest.mock import Mock

import pytest

from src.error_codes import ErrorCode
from src.http_client import HttpClient, HttpResponse
from src.oauth_providers.aws import AWSProvider
from src.oauth_providers.base import TokenAcquisitionError


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


def test_aws_provider_instance_profile_mode() -> None:
    """Test AWSProvider with instance profile enabled."""
    config = {
        "ClientId": "test-key",
        "ClientSecret": "test-secret",
        "TokenEndpoint": "https://sts.amazonaws.com/",
        "UseInstanceProfile": True,
    }

    # Should log info about instance profile support
    provider = AWSProvider(config)
    assert provider.use_instance_profile is True
    assert provider.service == "medical-imaging"


def test_aws_provider_acquire_token_success() -> None:
    """Test successful token acquisition."""
    # Create mock HTTP client
    mock_client = Mock(spec=HttpClient)
    mock_client.post.return_value = HttpResponse(
        status_code=200,
        json_data={
            "access_token": "aws_test_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        },
    )

    config = {
        "Region": "us-east-1",
        "ClientId": "test-key",
        "ClientSecret": "test-secret",
        "TokenEndpoint": "https://sts.amazonaws.com/",
    }

    provider = AWSProvider(config, http_client=mock_client)
    token = provider.acquire_token()

    assert token.access_token == "aws_test_token"
    assert token.expires_in == 3600
    mock_client.post.assert_called_once()


def test_aws_provider_acquire_token_handles_token_acquisition_error() -> None:
    """Test that TokenAcquisitionError is properly logged and re-raised."""
    mock_client = Mock(spec=HttpClient)
    # Simulate an error response that triggers TokenAcquisitionError
    mock_client.post.return_value = HttpResponse(
        status_code=200,
        json_data={"error": "invalid_client"},  # Missing access_token
    )

    config = {
        "ClientId": "test-key",
        "ClientSecret": "test-secret",
        "TokenEndpoint": "https://sts.amazonaws.com/",
    }

    provider = AWSProvider(config, http_client=mock_client)

    with pytest.raises(TokenAcquisitionError) as exc_info:
        provider.acquire_token()

    assert exc_info.value.error_code == ErrorCode.TOKEN_INVALID_RESPONSE


def test_aws_provider_acquire_token_handles_unexpected_error() -> None:
    """Test that unexpected errors are caught and wrapped."""
    mock_client = Mock(spec=HttpClient)
    # Simulate an unexpected error
    mock_client.post.side_effect = ValueError("Unexpected error")

    config = {
        "ClientId": "test-key",
        "ClientSecret": "test-secret",
        "TokenEndpoint": "https://sts.amazonaws.com/",
    }

    provider = AWSProvider(config, http_client=mock_client)

    with pytest.raises(TokenAcquisitionError) as exc_info:
        provider.acquire_token()

    assert exc_info.value.error_code == ErrorCode.TOKEN_ACQUISITION_FAILED
    assert "AWS authentication failed" in str(exc_info.value)
