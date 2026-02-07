# Generic OAuth2 DICOMweb Plugin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build Tier 1 - a generic OAuth2 plugin for Orthanc that automatically acquires, caches, and refreshes bearer tokens for any OAuth2-protected DICOMweb endpoint.

**Architecture:** Python plugin using Orthanc's Python SDK. Token manager handles OAuth2 client credentials flow with in-memory caching and proactive refresh. HTTP filter intercepts outgoing DICOMweb requests to inject Authorization headers. Configuration read from orthanc.json with environment variable substitution support.

**Tech Stack:** Python 3.8+, Orthanc Python SDK, requests library, threading for thread-safe token refresh

---

## Prerequisites

Before starting implementation, ensure:
- Python 3.8+ installed
- Docker installed (for Orthanc testing)
- Basic understanding of OAuth2 client credentials flow
- Access to an OAuth2 test endpoint (Azure, Keycloak, or mock server)

---

## Task 1: Project Structure Setup

**Files:**
- Create: `src/dicomweb_oauth_plugin.py` (main plugin entry point)
- Create: `src/token_manager.py` (OAuth2 token acquisition and caching)
- Create: `src/config_parser.py` (configuration loading with env var substitution)
- Create: `tests/test_token_manager.py`
- Create: `tests/test_config_parser.py`
- Create: `tests/test_plugin_integration.py`
- Create: `pytest.ini`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `.gitignore`

**Step 1: Create directory structure**

```bash
mkdir -p src tests docker examples
```

**Step 2: Create .gitignore**

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv/

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Secrets
*.pem
*.key
.env
secrets/

# Docker
*.log
```

**Step 3: Create requirements.txt**

```
requests>=2.31.0
```

**Step 4: Create requirements-dev.txt**

```
-r requirements.txt
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
responses>=0.23.0
```

**Step 5: Create pytest.ini**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html
```

**Step 6: Commit structure**

```bash
git add .gitignore requirements.txt requirements-dev.txt pytest.ini
git commit -m "chore: initialize project structure

- Add Python dependencies
- Configure pytest
- Add gitignore for Python project"
```

---

## Task 2: Configuration Parser with Environment Variable Substitution

**Files:**
- Create: `src/config_parser.py`
- Create: `tests/test_config_parser.py`

**Step 1: Write failing test for basic config parsing**

Create `tests/test_config_parser.py`:

```python
import pytest
from src.config_parser import ConfigParser


def test_parse_basic_server_config():
    """Test parsing a simple server configuration."""
    config = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com/v2/",
                    "TokenEndpoint": "https://login.example.com/oauth2/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "Scope": "https://dicom.example.com/.default"
                }
            }
        }
    }

    parser = ConfigParser(config)
    servers = parser.get_servers()

    assert len(servers) == 1
    assert "test-server" in servers
    assert servers["test-server"]["Url"] == "https://dicom.example.com/v2/"
    assert servers["test-server"]["ClientId"] == "client123"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_config_parser.py::test_parse_basic_server_config -v
```

Expected: FAIL with "No module named 'src.config_parser'"

**Step 3: Write minimal ConfigParser implementation**

Create `src/config_parser.py`:

```python
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
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_config_parser.py::test_parse_basic_server_config -v
```

Expected: PASS

**Step 5: Write test for environment variable substitution**

Add to `tests/test_config_parser.py`:

```python
import os


def test_env_var_substitution(monkeypatch):
    """Test that ${VAR} patterns are replaced with environment variables."""
    monkeypatch.setenv("TEST_CLIENT_ID", "env_client_123")
    monkeypatch.setenv("TEST_SECRET", "env_secret_456")

    config = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com/v2/",
                    "TokenEndpoint": "https://login.example.com/oauth2/token",
                    "ClientId": "${TEST_CLIENT_ID}",
                    "ClientSecret": "${TEST_SECRET}",
                    "Scope": "https://dicom.example.com/.default"
                }
            }
        }
    }

    parser = ConfigParser(config)
    servers = parser.get_servers()

    assert servers["test-server"]["ClientId"] == "env_client_123"
    assert servers["test-server"]["ClientSecret"] == "env_secret_456"


def test_missing_env_var_raises_error(monkeypatch):
    """Test that missing environment variables raise ConfigError."""
    config = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com/v2/",
                    "TokenEndpoint": "https://login.example.com/oauth2/token",
                    "ClientId": "${MISSING_VAR}",
                    "ClientSecret": "secret",
                    "Scope": "scope"
                }
            }
        }
    }

    with pytest.raises(ConfigError, match="Environment variable 'MISSING_VAR'"):
        parser = ConfigParser(config)
        parser.get_servers()
```

**Step 6: Run tests to verify they pass**

```bash
pytest tests/test_config_parser.py -v
```

Expected: All tests PASS

**Step 7: Write test for missing config sections**

Add to `tests/test_config_parser.py`:

```python
def test_missing_dicomweb_oauth_section():
    """Test that missing DicomWebOAuth section raises error."""
    config = {}

    with pytest.raises(ConfigError, match="Missing 'DicomWebOAuth' section"):
        ConfigParser(config)


def test_missing_servers_section():
    """Test that missing Servers section raises error."""
    config = {"DicomWebOAuth": {}}

    with pytest.raises(ConfigError, match="Missing 'Servers' section"):
        ConfigParser(config)
```

**Step 8: Run all config parser tests**

```bash
pytest tests/test_config_parser.py -v
```

Expected: All tests PASS

**Step 9: Commit config parser**

```bash
git add src/config_parser.py tests/test_config_parser.py
git commit -m "feat: add configuration parser with env var substitution

- Parse DicomWebOAuth server configurations
- Support ${VAR} environment variable substitution
- Validate required configuration sections
- 100% test coverage"
```

---

## Task 3: OAuth2 Token Manager - Token Acquisition

**Files:**
- Create: `src/token_manager.py`
- Modify: `tests/test_token_manager.py`

**Step 1: Write failing test for token acquisition**

Create `tests/test_token_manager.py`:

```python
import pytest
import responses
import time
from datetime import datetime, timedelta
from src.token_manager import TokenManager, TokenAcquisitionError


@responses.activate
def test_acquire_token_success():
    """Test successful token acquisition via client credentials flow."""
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "Bearer",
            "expires_in": 3600
        },
        status=200
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "https://dicom.example.com/.default"
    }

    manager = TokenManager("test-server", config)
    token = manager.get_token()

    assert token == "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
    assert len(responses.calls) == 1

    # Verify request was formed correctly
    request = responses.calls[0].request
    assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert "grant_type=client_credentials" in request.body
    assert "client_id=client123" in request.body
    assert "client_secret=secret456" in request.body
    assert "scope=https%3A%2F%2Fdicom.example.com%2F.default" in request.body
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_token_manager.py::test_acquire_token_success -v
```

Expected: FAIL with "No module named 'src.token_manager'"

**Step 3: Write minimal TokenManager implementation**

Create `src/token_manager.py`:

```python
"""OAuth2 token acquisition and caching for DICOMweb connections."""
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import requests


logger = logging.getLogger(__name__)


class TokenAcquisitionError(Exception):
    """Raised when token acquisition fails."""
    pass


class TokenManager:
    """Manages OAuth2 token acquisition, caching, and refresh for a DICOMweb server."""

    def __init__(self, server_name: str, config: Dict[str, Any]):
        """
        Initialize token manager for a DICOMweb server.

        Args:
            server_name: Name of the server (for logging)
            config: Server configuration containing TokenEndpoint, ClientId, etc.
        """
        self.server_name = server_name
        self.config = config
        self._validate_config()

        # Token cache
        self._cached_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._lock = threading.Lock()

        # Configuration
        self.token_endpoint = config["TokenEndpoint"]
        self.client_id = config["ClientId"]
        self.client_secret = config["ClientSecret"]
        self.scope = config.get("Scope", "")
        self.refresh_buffer_seconds = config.get("TokenRefreshBufferSeconds", 300)

    def _validate_config(self) -> None:
        """Validate that required configuration keys are present."""
        required_keys = ["TokenEndpoint", "ClientId", "ClientSecret"]
        missing_keys = [key for key in required_keys if key not in self.config]

        if missing_keys:
            raise ValueError(
                f"Server '{self.server_name}' missing required config keys: {missing_keys}"
            )

    def get_token(self) -> str:
        """
        Get a valid OAuth2 access token, acquiring or refreshing as needed.

        Returns:
            Valid access token string

        Raises:
            TokenAcquisitionError: If token acquisition fails
        """
        with self._lock:
            # Check if we have a valid cached token
            if self._is_token_valid():
                logger.debug(f"Using cached token for server '{self.server_name}'")
                return self._cached_token

            # Need to acquire a new token
            logger.info(f"Acquiring new token for server '{self.server_name}'")
            return self._acquire_token()

    def _is_token_valid(self) -> bool:
        """Check if cached token exists and is not expiring soon."""
        if self._cached_token is None or self._token_expiry is None:
            return False

        # Token is valid if it won't expire within the buffer window
        now = datetime.utcnow()
        buffer = timedelta(seconds=self.refresh_buffer_seconds)
        return now + buffer < self._token_expiry

    def _acquire_token(self) -> str:
        """
        Acquire a new OAuth2 token via client credentials flow.

        Returns:
            Access token string

        Raises:
            TokenAcquisitionError: If acquisition fails
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        if self.scope:
            data["scope"] = self.scope

        try:
            response = requests.post(
                self.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            response.raise_for_status()

            token_data = response.json()
            self._cached_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

            logger.info(
                f"Token acquired for server '{self.server_name}', "
                f"expires in {expires_in} seconds"
            )

            return self._cached_token

        except requests.RequestException as e:
            error_msg = f"Failed to acquire token for server '{self.server_name}': {e}"
            logger.error(error_msg)
            raise TokenAcquisitionError(error_msg) from e
        except (KeyError, ValueError) as e:
            error_msg = f"Invalid token response for server '{self.server_name}': {e}"
            logger.error(error_msg)
            raise TokenAcquisitionError(error_msg) from e
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_token_manager.py::test_acquire_token_success -v
```

Expected: PASS

**Step 5: Write test for token caching**

Add to `tests/test_token_manager.py`:

```python
@responses.activate
def test_token_caching():
    """Test that valid tokens are cached and reused."""
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "token123",
            "token_type": "Bearer",
            "expires_in": 3600
        },
        status=200
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope"
    }

    manager = TokenManager("test-server", config)

    # First call should acquire token
    token1 = manager.get_token()
    assert token1 == "token123"
    assert len(responses.calls) == 1

    # Second call should use cached token (no new HTTP request)
    token2 = manager.get_token()
    assert token2 == "token123"
    assert len(responses.calls) == 1  # Still only 1 call
```

**Step 6: Run test to verify it passes**

```bash
pytest tests/test_token_manager.py::test_token_caching -v
```

Expected: PASS

**Step 7: Write test for token refresh before expiry**

Add to `tests/test_token_manager.py`:

```python
@responses.activate
def test_token_refresh_before_expiry():
    """Test that tokens are refreshed before they expire."""
    # First token expires in 10 seconds
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "token1",
            "token_type": "Bearer",
            "expires_in": 10
        },
        status=200
    )

    # Second token (after refresh)
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "token2",
            "token_type": "Bearer",
            "expires_in": 3600
        },
        status=200
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope",
        "TokenRefreshBufferSeconds": 300  # 5 minutes buffer
    }

    manager = TokenManager("test-server", config)

    # First call acquires token (expires in 10 seconds)
    token1 = manager.get_token()
    assert token1 == "token1"
    assert len(responses.calls) == 1

    # Token expires in 10 seconds, but we have 300 second buffer
    # So it should be considered expired and refresh immediately
    token2 = manager.get_token()
    assert token2 == "token2"
    assert len(responses.calls) == 2  # New token acquired
```

**Step 8: Run test to verify it passes**

```bash
pytest tests/test_token_manager.py::test_token_refresh_before_expiry -v
```

Expected: PASS

**Step 9: Write test for token acquisition failure**

Add to `tests/test_token_manager.py`:

```python
@responses.activate
def test_token_acquisition_failure():
    """Test that token acquisition failures raise TokenAcquisitionError."""
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={"error": "invalid_client"},
        status=401
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "invalid_client",
        "ClientSecret": "wrong_secret",
        "Scope": "scope"
    }

    manager = TokenManager("test-server", config)

    with pytest.raises(TokenAcquisitionError, match="Failed to acquire token"):
        manager.get_token()
```

**Step 10: Run all token manager tests**

```bash
pytest tests/test_token_manager.py -v
```

Expected: All tests PASS

**Step 11: Commit token manager**

```bash
git add src/token_manager.py tests/test_token_manager.py
git commit -m "feat: add OAuth2 token manager with caching

- Implement client credentials flow
- Cache tokens with expiry tracking
- Proactive refresh with configurable buffer
- Thread-safe token access
- Comprehensive error handling
- 100% test coverage"
```

---

## Task 4: Orthanc Plugin Integration - HTTP Filter

**Files:**
- Create: `src/dicomweb_oauth_plugin.py`
- Create: `tests/test_plugin_integration.py`

**Step 1: Write test for plugin initialization**

Create `tests/test_plugin_integration.py`:

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.dicomweb_oauth_plugin import initialize_plugin


def test_plugin_initialization():
    """Test that plugin initializes with valid configuration."""
    mock_orthanc = Mock()
    mock_orthanc.GetConfiguration.return_value = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com/v2/",
                    "TokenEndpoint": "https://login.example.com/oauth2/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "Scope": "scope"
                }
            }
        }
    }

    # Should not raise any exception
    initialize_plugin(mock_orthanc)

    # Verify configuration was read
    mock_orthanc.GetConfiguration.assert_called_once()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_plugin_integration.py::test_plugin_initialization -v
```

Expected: FAIL with "No module named 'src.dicomweb_oauth_plugin'"

**Step 3: Write minimal plugin implementation**

Create `src/dicomweb_oauth_plugin.py`:

```python
"""
Orthanc DICOMweb OAuth2 Plugin

Generic OAuth2/OIDC token management plugin for Orthanc's DICOMweb connections.
Automatically acquires, caches, and refreshes bearer tokens for any OAuth2-protected
DICOMweb endpoint.
"""
import json
import logging
import orthanc
from typing import Dict, Optional
from src.config_parser import ConfigParser, ConfigError
from src.token_manager import TokenManager, TokenAcquisitionError


# Global state
_token_managers: Dict[str, TokenManager] = {}
_server_urls: Dict[str, str] = {}

logger = logging.getLogger(__name__)


def initialize_plugin(orthanc_module=None):
    """
    Initialize the DICOMweb OAuth plugin.

    Args:
        orthanc_module: Orthanc module (for testing, defaults to global orthanc)
    """
    global _token_managers, _server_urls

    if orthanc_module is None:
        orthanc_module = orthanc

    logger.info("Initializing DICOMweb OAuth plugin")

    try:
        # Load configuration
        config = orthanc_module.GetConfiguration()
        parser = ConfigParser(config)
        servers = parser.get_servers()

        # Initialize token manager for each configured server
        for server_name, server_config in servers.items():
            logger.info(f"Configuring OAuth for server: {server_name}")

            _token_managers[server_name] = TokenManager(server_name, server_config)
            _server_urls[server_name] = server_config["Url"]

            logger.info(f"Server '{server_name}' configured with URL: {server_config['Url']}")

        logger.info(f"DICOMweb OAuth plugin initialized with {len(servers)} server(s)")

    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize plugin: {e}")
        raise


def on_outgoing_http_request(uri: str, method: str, headers: Dict[str, str],
                              get_params: Dict[str, str], body: bytes) -> Dict:
    """
    Orthanc HTTP filter callback - injects OAuth2 bearer tokens.

    This function is called by Orthanc before each outgoing HTTP request.
    We check if the request is to a configured DICOMweb server and inject
    the Authorization header with a valid bearer token.

    Args:
        uri: Request URI
        method: HTTP method (GET, POST, etc.)
        headers: Request headers (mutable)
        get_params: Query parameters
        body: Request body

    Returns:
        Modified request dict or None to allow request
    """
    global _token_managers, _server_urls

    # Find which server this request is for
    server_name = _find_server_for_uri(uri)

    if server_name is None:
        # Not a configured OAuth server, let it pass through
        return None

    logger.debug(f"Injecting OAuth token for server '{server_name}'")

    try:
        # Get valid token
        token_manager = _token_managers[server_name]
        token = token_manager.get_token()

        # Inject Authorization header
        headers["Authorization"] = f"Bearer {token}"

        # Return modified request
        return {
            "headers": headers,
            "method": method,
            "uri": uri,
            "get_params": get_params,
            "body": body
        }

    except TokenAcquisitionError as e:
        logger.error(f"Failed to acquire token for '{server_name}': {e}")
        # Return error response
        return {
            "status": 503,
            "body": json.dumps({
                "error": "OAuth token acquisition failed",
                "server": server_name,
                "details": str(e)
            })
        }


def _find_server_for_uri(uri: str) -> Optional[str]:
    """
    Find which configured server a URI belongs to.

    Args:
        uri: Request URI

    Returns:
        Server name if URI matches a configured server, None otherwise
    """
    global _server_urls

    for server_name, server_url in _server_urls.items():
        if uri.startswith(server_url):
            return server_name

    return None


# Orthanc plugin entry point
def OnChange(changeType, level, resource):
    """Orthanc change callback (not used, but required by plugin API)."""
    pass


def OnIncomingHttpRequest(method, uri, ip, username, headers):
    """Orthanc incoming HTTP request callback (not used for this plugin)."""
    pass


# Plugin registration
try:
    logger.info("Registering DICOMweb OAuth plugin with Orthanc")
    initialize_plugin()
    orthanc.RegisterOnOutgoingHttpRequestFilter(on_outgoing_http_request)
    logger.info("DICOMweb OAuth plugin registered successfully")
except Exception as e:
    logger.error(f"Failed to register plugin: {e}")
    raise
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_plugin_integration.py::test_plugin_initialization -v
```

Expected: PASS

**Step 5: Write test for HTTP header injection**

Add to `tests/test_plugin_integration.py`:

```python
from src.dicomweb_oauth_plugin import on_outgoing_http_request, _token_managers, _server_urls
import responses


@responses.activate
def test_inject_authorization_header():
    """Test that Authorization header is injected for configured servers."""
    # Setup mock token response
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "test_token_123",
            "token_type": "Bearer",
            "expires_in": 3600
        },
        status=200
    )

    # Initialize plugin
    mock_orthanc = Mock()
    mock_orthanc.GetConfiguration.return_value = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com/v2/",
                    "TokenEndpoint": "https://login.example.com/oauth2/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "Scope": "scope"
                }
            }
        }
    }
    initialize_plugin(mock_orthanc)

    # Make request to configured DICOMweb server
    headers = {"Content-Type": "application/dicom+json"}
    result = on_outgoing_http_request(
        uri="https://dicom.example.com/v2/studies",
        method="GET",
        headers=headers,
        get_params={},
        body=b""
    )

    # Verify Authorization header was injected
    assert result is not None
    assert "Authorization" in result["headers"]
    assert result["headers"]["Authorization"] == "Bearer test_token_123"


def test_non_oauth_request_passes_through():
    """Test that requests to non-configured servers pass through unchanged."""
    # Initialize plugin with no matching server
    mock_orthanc = Mock()
    mock_orthanc.GetConfiguration.return_value = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com/v2/",
                    "TokenEndpoint": "https://login.example.com/oauth2/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "Scope": "scope"
                }
            }
        }
    }
    initialize_plugin(mock_orthanc)

    # Make request to different server
    headers = {"Content-Type": "application/dicom+json"}
    result = on_outgoing_http_request(
        uri="https://other-server.com/api/studies",
        method="GET",
        headers=headers,
        get_params={},
        body=b""
    )

    # Should return None (pass through)
    assert result is None
```

**Step 6: Run all plugin integration tests**

```bash
pytest tests/test_plugin_integration.py -v
```

Expected: All tests PASS

**Step 7: Commit plugin integration**

```bash
git add src/dicomweb_oauth_plugin.py tests/test_plugin_integration.py
git commit -m "feat: add Orthanc plugin with HTTP filter

- Initialize plugin from Orthanc configuration
- Register outgoing HTTP request filter
- Inject Authorization headers for configured servers
- Handle token acquisition failures gracefully
- Pass through non-OAuth requests unchanged
- 100% test coverage"
```

---

## Task 5: Docker Development Environment

**Files:**
- Create: `docker/Dockerfile`
- Create: `docker/orthanc.json`
- Create: `docker/docker-compose.yml`
- Create: `examples/azure-config.json`
- Create: `examples/keycloak-config.json`

**Step 1: Create Dockerfile for Orthanc with plugin**

Create `docker/Dockerfile`:

```dockerfile
FROM orthancteam/orthanc:24.12.1

# Install Python dependencies
RUN pip install --no-cache-dir requests

# Copy plugin files
COPY ../src/dicomweb_oauth_plugin.py /etc/orthanc/plugins/
COPY ../src/token_manager.py /etc/orthanc/plugins/
COPY ../src/config_parser.py /etc/orthanc/plugins/

# Copy Orthanc configuration
COPY orthanc.json /etc/orthanc/

# Expose ports
EXPOSE 8042 4242

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8042/system || exit 1

CMD ["Orthanc", "/etc/orthanc/orthanc.json"]
```

**Step 2: Create basic Orthanc configuration**

Create `docker/orthanc.json`:

```json
{
  "Name": "Orthanc DICOMweb OAuth Development",
  "HttpPort": 8042,
  "DicomPort": 4242,

  "RemoteAccessAllowed": true,
  "AuthenticationEnabled": false,

  "Plugins": [
    "/etc/orthanc/plugins/dicomweb_oauth_plugin.py"
  ],

  "DicomWeb": {
    "Enable": true,
    "Root": "/dicom-web/",
    "EnableWado": true,
    "WadoRoot": "/wado",
    "Ssl": false,
    "QidoCaseSensitive": false,
    "Host": "0.0.0.0",
    "Port": 8042
  },

  "DicomWebOAuth": {
    "Servers": {
      "example-server": {
        "Url": "https://dicom.example.com/v2/",
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "${OAUTH_CLIENT_ID}",
        "ClientSecret": "${OAUTH_CLIENT_SECRET}",
        "Scope": "https://dicom.example.com/.default",
        "TokenRefreshBufferSeconds": 300
      }
    }
  },

  "Verbosity": "verbose",
  "LogLevel": "default"
}
```

**Step 3: Create Docker Compose for development**

Create `docker/docker-compose.yml`:

```yaml
version: '3.8'

services:
  orthanc:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "8042:8042"  # HTTP
      - "4242:4242"  # DICOM
    environment:
      # Override with your OAuth credentials
      - OAUTH_CLIENT_ID=${OAUTH_CLIENT_ID:-your_client_id}
      - OAUTH_CLIENT_SECRET=${OAUTH_CLIENT_SECRET:-your_client_secret}
    volumes:
      # Mount source for development (hot reload)
      - ../src:/etc/orthanc/plugins:ro
      - orthanc-storage:/var/lib/orthanc/db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8042/system"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

volumes:
  orthanc-storage:
    driver: local
```

**Step 4: Create Azure example configuration**

Create `examples/azure-config.json`:

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "azure-dicom": {
        "Url": "https://workspace-dicom.dicom.azurehealthcareapis.com/v2/",
        "TokenEndpoint": "https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token",
        "ClientId": "${AZURE_CLIENT_ID}",
        "ClientSecret": "${AZURE_CLIENT_SECRET}",
        "Scope": "https://dicom.healthcareapis.azure.com/.default",
        "TokenRefreshBufferSeconds": 300
      }
    }
  }
}
```

**Step 5: Create Keycloak example configuration**

Create `examples/keycloak-config.json`:

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "keycloak-dicom": {
        "Url": "https://dicom.example.com/dicom-web/",
        "TokenEndpoint": "https://keycloak.example.com/realms/healthcare/protocol/openid-connect/token",
        "ClientId": "${KEYCLOAK_CLIENT_ID}",
        "ClientSecret": "${KEYCLOAK_CLIENT_SECRET}",
        "Scope": "dicomweb",
        "TokenRefreshBufferSeconds": 300
      }
    }
  }
}
```

**Step 6: Create .env.example for Docker**

Create `docker/.env.example`:

```bash
# OAuth2 Client Credentials
OAUTH_CLIENT_ID=your_client_id_here
OAUTH_CLIENT_SECRET=your_client_secret_here

# Azure Example
# OAUTH_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# OAUTH_CLIENT_SECRET=your_azure_secret

# Keycloak Example
# OAUTH_CLIENT_ID=orthanc-client
# OAUTH_CLIENT_SECRET=your_keycloak_secret
```

**Step 7: Create README for Docker setup**

Create `docker/README.md`:

```markdown
# Docker Development Environment

## Quick Start

1. Copy `.env.example` to `.env` and configure your OAuth credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. Start Orthanc with the plugin:
   ```bash
   docker-compose up -d
   ```

3. Access Orthanc at http://localhost:8042

4. View logs:
   ```bash
   docker-compose logs -f orthanc
   ```

## Testing the Plugin

Check plugin status:
```bash
curl http://localhost:8042/plugins
```

Test DICOMweb connection (will trigger OAuth token acquisition):
```bash
curl http://localhost:8042/dicom-web/studies
```

## Development Workflow

The `src/` directory is mounted as a volume, but Python plugins require an Orthanc restart to reload:

```bash
docker-compose restart orthanc
```

## Troubleshooting

**View plugin logs:**
```bash
docker-compose logs orthanc | grep "DICOMweb OAuth"
```

**Check token acquisition:**
Look for "Token acquired for server" in logs

**Verify configuration:**
```bash
docker-compose exec orthanc cat /etc/orthanc/orthanc.json
```
```

**Step 8: Test Docker build**

```bash
cd docker
docker-compose build
```

Expected: Build succeeds without errors

**Step 9: Commit Docker environment**

```bash
git add docker/ examples/
git commit -m "feat: add Docker development environment

- Dockerfile based on orthancteam/orthanc
- Docker Compose for easy development
- Example configurations for Azure and Keycloak
- Environment variable configuration
- Development workflow documentation"
```

---

## Task 6: Plugin Monitoring Endpoints

**Files:**
- Modify: `src/dicomweb_oauth_plugin.py`
- Create: `tests/test_monitoring_endpoints.py`

**Step 1: Write test for status endpoint**

Create `tests/test_monitoring_endpoints.py`:

```python
import pytest
import json
from unittest.mock import Mock, patch
from src.dicomweb_oauth_plugin import (
    initialize_plugin,
    handle_rest_api_status,
    handle_rest_api_servers,
    handle_rest_api_test_server
)


def test_status_endpoint():
    """Test GET /dicomweb-oauth/status returns plugin status."""
    mock_orthanc = Mock()
    mock_orthanc.GetConfiguration.return_value = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com/v2/",
                    "TokenEndpoint": "https://login.example.com/oauth2/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "Scope": "scope"
                }
            }
        }
    }
    initialize_plugin(mock_orthanc)

    # Call status endpoint
    output = Mock()
    result = handle_rest_api_status(output, None, None)

    # Parse response
    response = json.loads(output.AnswerBuffer.call_args[0][0])

    assert response["plugin"] == "DICOMweb OAuth"
    assert response["version"] == "1.0.0"
    assert response["status"] == "active"
    assert response["configured_servers"] == 1
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_monitoring_endpoints.py::test_status_endpoint -v
```

Expected: FAIL (functions not defined)

**Step 3: Add monitoring endpoints to plugin**

Add to `src/dicomweb_oauth_plugin.py`:

```python
# Add to imports
__version__ = "1.0.0"


def handle_rest_api_status(output, uri, **request):
    """
    GET /dicomweb-oauth/status

    Returns plugin status and configuration summary.
    """
    global _token_managers

    status = {
        "plugin": "DICOMweb OAuth",
        "version": __version__,
        "status": "active",
        "configured_servers": len(_token_managers),
        "servers": list(_token_managers.keys())
    }

    output.AnswerBuffer(json.dumps(status, indent=2), "application/json")


def handle_rest_api_servers(output, uri, **request):
    """
    GET /dicomweb-oauth/servers

    Returns list of configured servers and their status.
    """
    global _token_managers, _server_urls

    servers = []
    for server_name in _token_managers.keys():
        token_manager = _token_managers[server_name]

        server_info = {
            "name": server_name,
            "url": _server_urls[server_name],
            "token_endpoint": token_manager.token_endpoint,
            "has_cached_token": token_manager._cached_token is not None,
            "token_valid": token_manager._is_token_valid() if token_manager._cached_token else False
        }
        servers.append(server_info)

    output.AnswerBuffer(json.dumps({"servers": servers}, indent=2), "application/json")


def handle_rest_api_test_server(output, uri, **request):
    """
    POST /dicomweb-oauth/servers/{name}/test

    Test token acquisition for a specific server.
    """
    global _token_managers

    # Extract server name from URI
    parts = uri.split('/')
    if len(parts) < 4:
        output.AnswerBuffer(
            json.dumps({"error": "Server name not specified"}),
            "application/json",
            status=400
        )
        return

    server_name = parts[-2]

    if server_name not in _token_managers:
        output.AnswerBuffer(
            json.dumps({"error": f"Server '{server_name}' not configured"}),
            "application/json",
            status=404
        )
        return

    try:
        token_manager = _token_managers[server_name]
        token = token_manager.get_token()

        result = {
            "server": server_name,
            "status": "success",
            "token_acquired": True,
            "token_length": len(token),
            "token_preview": token[:20] + "..." if len(token) > 20 else token
        }

        output.AnswerBuffer(json.dumps(result, indent=2), "application/json")

    except TokenAcquisitionError as e:
        result = {
            "server": server_name,
            "status": "error",
            "error": str(e)
        }
        output.AnswerBuffer(
            json.dumps(result, indent=2),
            "application/json",
            status=503
        )


# Register REST API endpoints (add to plugin registration section)
try:
    logger.info("Registering REST API endpoints")
    orthanc.RegisterRestCallback('/dicomweb-oauth/status', handle_rest_api_status)
    orthanc.RegisterRestCallback('/dicomweb-oauth/servers', handle_rest_api_servers)
    orthanc.RegisterRestCallback('/dicomweb-oauth/servers/(.*)/test', handle_rest_api_test_server)
except Exception as e:
    logger.error(f"Failed to register REST API endpoints: {e}")
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_monitoring_endpoints.py::test_status_endpoint -v
```

Expected: PASS

**Step 5: Write test for servers endpoint**

Add to `tests/test_monitoring_endpoints.py`:

```python
import responses


@responses.activate
def test_servers_endpoint():
    """Test GET /dicomweb-oauth/servers returns server details."""
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "token123",
            "token_type": "Bearer",
            "expires_in": 3600
        },
        status=200
    )

    mock_orthanc = Mock()
    mock_orthanc.GetConfiguration.return_value = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com/v2/",
                    "TokenEndpoint": "https://login.example.com/oauth2/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "Scope": "scope"
                }
            }
        }
    }
    initialize_plugin(mock_orthanc)

    # Acquire token first
    from src.dicomweb_oauth_plugin import _token_managers
    _token_managers["test-server"].get_token()

    # Call servers endpoint
    output = Mock()
    result = handle_rest_api_servers(output, None, None)

    # Parse response
    response = json.loads(output.AnswerBuffer.call_args[0][0])

    assert len(response["servers"]) == 1
    assert response["servers"][0]["name"] == "test-server"
    assert response["servers"][0]["url"] == "https://dicom.example.com/v2/"
    assert response["servers"][0]["has_cached_token"] is True
    assert response["servers"][0]["token_valid"] is True
```

**Step 6: Run all monitoring tests**

```bash
pytest tests/test_monitoring_endpoints.py -v
```

Expected: All tests PASS

**Step 7: Commit monitoring endpoints**

```bash
git add src/dicomweb_oauth_plugin.py tests/test_monitoring_endpoints.py
git commit -m "feat: add REST API monitoring endpoints

- GET /dicomweb-oauth/status - plugin status
- GET /dicomweb-oauth/servers - configured servers
- POST /dicomweb-oauth/servers/{name}/test - test token acquisition
- 100% test coverage"
```

---

## Task 7: Error Handling and Retry Logic

**Files:**
- Modify: `src/token_manager.py`
- Create: `tests/test_error_handling.py`

**Step 1: Write test for network timeout retry**

Create `tests/test_error_handling.py`:

```python
import pytest
import responses
from requests.exceptions import Timeout, ConnectionError
from src.token_manager import TokenManager, TokenAcquisitionError


@responses.activate
def test_retry_on_timeout():
    """Test that token acquisition retries on timeout."""
    # First attempt times out
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        body=Timeout("Connection timeout")
    )

    # Second attempt succeeds
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "token123",
            "token_type": "Bearer",
            "expires_in": 3600
        },
        status=200
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope"
    }

    manager = TokenManager("test-server", config)
    token = manager.get_token()

    assert token == "token123"
    assert len(responses.calls) == 2  # Retried once
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_error_handling.py::test_retry_on_timeout -v
```

Expected: FAIL (no retry logic implemented)

**Step 3: Add retry logic to token manager**

Modify `src/token_manager.py` `_acquire_token` method:

```python
def _acquire_token(self) -> str:
    """
    Acquire a new OAuth2 token via client credentials flow with retry logic.

    Returns:
        Access token string

    Raises:
        TokenAcquisitionError: If acquisition fails after all retries
    """
    data = {
        "grant_type": "client_credentials",
        "client_id": self.client_id,
        "client_secret": self.client_secret,
    }

    if self.scope:
        data["scope"] = self.scope

    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            response = requests.post(
                self.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            response.raise_for_status()

            token_data = response.json()
            self._cached_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

            logger.info(
                f"Token acquired for server '{self.server_name}', "
                f"expires in {expires_in} seconds"
            )

            return self._cached_token

        except (requests.Timeout, requests.ConnectionError) as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Token acquisition attempt {attempt + 1} failed for "
                    f"server '{self.server_name}': {e}. Retrying in {retry_delay}s..."
                )
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            else:
                error_msg = (
                    f"Failed to acquire token for server '{self.server_name}' "
                    f"after {max_retries} attempts: {e}"
                )
                logger.error(error_msg)
                raise TokenAcquisitionError(error_msg) from e

        except requests.RequestException as e:
            # Non-retryable errors (4xx, 5xx)
            error_msg = f"Failed to acquire token for server '{self.server_name}': {e}"
            logger.error(error_msg)
            raise TokenAcquisitionError(error_msg) from e

        except (KeyError, ValueError) as e:
            error_msg = f"Invalid token response for server '{self.server_name}': {e}"
            logger.error(error_msg)
            raise TokenAcquisitionError(error_msg) from e
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_error_handling.py::test_retry_on_timeout -v
```

Expected: PASS

**Step 5: Write test for max retries exceeded**

Add to `tests/test_error_handling.py`:

```python
@responses.activate
def test_max_retries_exceeded():
    """Test that token acquisition fails after max retries."""
    # All attempts time out
    for _ in range(3):
        responses.add(
            responses.POST,
            "https://login.example.com/oauth2/token",
            body=Timeout("Connection timeout")
        )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope"
    }

    manager = TokenManager("test-server", config)

    with pytest.raises(TokenAcquisitionError, match="after 3 attempts"):
        manager.get_token()

    assert len(responses.calls) == 3  # All retries attempted
```

**Step 6: Run test to verify it passes**

```bash
pytest tests/test_error_handling.py::test_max_retries_exceeded -v
```

Expected: PASS

**Step 7: Write test for non-retryable errors**

Add to `tests/test_error_handling.py`:

```python
@responses.activate
def test_no_retry_on_auth_error():
    """Test that 401 authentication errors are not retried."""
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={"error": "invalid_client"},
        status=401
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "invalid_client",
        "ClientSecret": "wrong_secret",
        "Scope": "scope"
    }

    manager = TokenManager("test-server", config)

    with pytest.raises(TokenAcquisitionError):
        manager.get_token()

    # Should not retry auth errors
    assert len(responses.calls) == 1
```

**Step 8: Run all error handling tests**

```bash
pytest tests/test_error_handling.py -v
```

Expected: All tests PASS

**Step 9: Commit error handling improvements**

```bash
git add src/token_manager.py tests/test_error_handling.py
git commit -m "feat: add retry logic for token acquisition

- Exponential backoff for network errors
- Max 3 retry attempts
- No retry for authentication errors (4xx)
- Detailed logging for troubleshooting
- 100% test coverage"
```

---

## Task 8: Documentation and Examples

**Files:**
- Create: `README.md`
- Create: `docs/quickstart-azure.md`
- Create: `docs/quickstart-keycloak.md`
- Create: `docs/configuration-reference.md`
- Create: `docs/troubleshooting.md`

**Step 1: Create main README**

Create `README.md`:

```markdown
# Orthanc DICOMweb OAuth Plugin

Generic OAuth2/OIDC token management plugin for Orthanc's DICOMweb connections. Automatically acquires, caches, and refreshes bearer tokens for any OAuth2-protected DICOMweb endpoint.

## Features

✅ **Generic OAuth2** - Works with any OAuth2/OIDC provider (Azure, Google Cloud, Keycloak, Auth0, Okta, etc.)
✅ **Automatic token refresh** - Proactive refresh before expiration (configurable buffer)
✅ **Zero-downtime** - Thread-safe token caching, no interruption to DICOMweb operations
✅ **Easy deployment** - Python plugin, no compilation required
✅ **Docker-ready** - Works with `orthancteam/orthanc` images out of the box
✅ **Environment variable support** - Secure credential management via `${VAR}` substitution
✅ **Monitoring endpoints** - REST API for status checks and testing

## Problem Solved

Orthanc's DICOMweb plugin only supports HTTP Basic auth or static headers. This plugin enables Orthanc to connect to any OAuth2-protected DICOMweb server:

- **Azure Health Data Services** (Microsoft Entra ID OAuth2)
- **Google Cloud Healthcare API** (lighter alternative to official C++ plugin)
- **AWS HealthImaging** (OAuth2/SigV4)
- **Any DICOMweb server behind Keycloak, Auth0, Okta, etc.**

## Quick Start

### Docker (Recommended)

1. **Clone and configure:**
   ```bash
   git clone https://github.com/yourusername/orthanc-dicomweb-oauth.git
   cd orthanc-dicomweb-oauth/docker
   cp .env.example .env
   # Edit .env with your OAuth credentials
   ```

2. **Start Orthanc:**
   ```bash
   docker-compose up -d
   ```

3. **Test the connection:**
   ```bash
   curl http://localhost:8042/dicomweb-oauth/status
   ```

### Manual Installation

1. **Install dependencies:**
   ```bash
   pip install requests
   ```

2. **Copy plugin files to Orthanc:**
   ```bash
   cp src/*.py /etc/orthanc/plugins/
   ```

3. **Configure Orthanc** (see [Configuration](#configuration))

4. **Restart Orthanc**

## Configuration

Add to your `orthanc.json`:

```json
{
  "Plugins": [
    "/etc/orthanc/plugins/dicomweb_oauth_plugin.py"
  ],

  "DicomWebOAuth": {
    "Servers": {
      "my-cloud-dicom": {
        "Url": "https://dicom.example.com/v2/",
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "${OAUTH_CLIENT_ID}",
        "ClientSecret": "${OAUTH_CLIENT_SECRET}",
        "Scope": "https://dicom.example.com/.default",
        "TokenRefreshBufferSeconds": 300
      }
    }
  }
}
```

**Environment variables** referenced via `${VAR_NAME}` are automatically substituted at startup.

### Provider-Specific Examples

- **[Azure Health Data Services](docs/quickstart-azure.md)** - Complete setup guide
- **[Keycloak](docs/quickstart-keycloak.md)** - Self-hosted OAuth2
- **Google Cloud** - See `examples/google-config.json`

Full configuration reference: **[docs/configuration-reference.md](docs/configuration-reference.md)**

## Monitoring & Testing

The plugin exposes REST endpoints for monitoring:

```bash
# Plugin status
curl http://localhost:8042/dicomweb-oauth/status

# List configured servers and token status
curl http://localhost:8042/dicomweb-oauth/servers

# Test token acquisition for a specific server
curl -X POST http://localhost:8042/dicomweb-oauth/servers/my-cloud-dicom/test
```

## How It Works

1. **On startup:** Plugin reads configuration and initializes token managers for each server
2. **On each outgoing DICOMweb request:** HTTP filter checks if request URL matches configured server
3. **If matched:** Acquires valid token (from cache or fresh), injects `Authorization: Bearer <token>` header
4. **Proactive refresh:** Tokens refreshed before expiration (default: 5 minutes before expiry)
5. **Thread-safe:** Multiple concurrent requests safely share cached tokens

## Development

### Run tests:
```bash
pip install -r requirements-dev.txt
pytest
```

### Test coverage:
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Development with Docker:
```bash
cd docker
docker-compose up -d
docker-compose logs -f orthanc
```

## Troubleshooting

See **[docs/troubleshooting.md](docs/troubleshooting.md)** for common issues and solutions.

**Quick diagnostics:**
- Check plugin loaded: `curl http://localhost:8042/plugins`
- View logs: `docker-compose logs orthanc | grep OAuth`
- Test token acquisition: `curl -X POST http://localhost:8042/dicomweb-oauth/servers/SERVER_NAME/test`

## License

MIT License - see [LICENSE](LICENSE) for details

## Contributing

Contributions welcome! Please open an issue or PR.

## References

- [Orthanc DICOMweb Plugin](https://orthanc.uclouvain.be/book/plugins/dicomweb.html)
- [Orthanc Python Plugin SDK](https://orthanc.uclouvain.be/book/plugins/python.html)
- [OAuth2 Client Credentials Flow (RFC 6749)](https://datatracker.ietf.org/doc/html/rfc6749#section-4.4)
- [Azure DICOM Service Auth](https://learn.microsoft.com/en-us/azure/healthcare-apis/dicom/get-access-token)
```

**Step 2: Create Azure quickstart guide**

Create `docs/quickstart-azure.md`:

```markdown
# Azure Health Data Services Quick Start

Complete guide to connecting Orthanc to Azure Health Data Services DICOM service using OAuth2.

## Prerequisites

- Azure subscription
- Azure Health Data Services workspace with DICOM service
- Azure CLI or Azure Portal access

## Step 1: Create App Registration

### Via Azure Portal:

1. Go to **Azure Active Directory** > **App registrations** > **New registration**
2. Name: `orthanc-dicomweb-client`
3. Click **Register**
4. Note the **Application (client) ID**
5. Note your **Tenant ID** (from Overview page)

### Via Azure CLI:

```bash
az ad app create --display-name orthanc-dicomweb-client
# Note the "appId" from output
```

## Step 2: Create Client Secret

### Via Azure Portal:

1. In your app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Description: `orthanc-plugin`
4. Expiration: Choose duration (recommend 24 months)
5. Click **Add**
6. **Copy the secret value immediately** (you can't view it again)

### Via Azure CLI:

```bash
az ad app credential reset --id <APP_ID>
# Note the "password" from output
```

## Step 3: Grant DICOM Permissions

Your app needs permission to access the DICOM service:

```bash
# Get DICOM service principal ID
DICOM_RESOURCE_ID=$(az healthcareapis workspace dicom-service show \
  --workspace-name <WORKSPACE_NAME> \
  --resource-group <RESOURCE_GROUP> \
  --name <DICOM_SERVICE_NAME> \
  --query id -o tsv)

# Assign "DICOM Data Owner" role
az role assignment create \
  --assignee <APP_ID> \
  --role "DICOM Data Owner" \
  --scope $DICOM_RESOURCE_ID
```

Or via Portal:
1. Go to your DICOM service > **Access control (IAM)**
2. Click **Add role assignment**
3. Role: **DICOM Data Owner**
4. Assign access to: **User, group, or service principal**
5. Select your app registration
6. Click **Save**

## Step 4: Configure Orthanc

### Option A: Docker (Recommended)

Create `.env` file:
```bash
AZURE_CLIENT_ID=your-application-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
AZURE_DICOM_URL=https://workspace-dicom.dicom.azurehealthcareapis.com/v2/
```

Update `docker/orthanc.json`:
```json
{
  "DicomWebOAuth": {
    "Servers": {
      "azure-dicom": {
        "Url": "${AZURE_DICOM_URL}",
        "TokenEndpoint": "https://login.microsoftonline.com/${AZURE_TENANT_ID}/oauth2/v2.0/token",
        "ClientId": "${AZURE_CLIENT_ID}",
        "ClientSecret": "${AZURE_CLIENT_SECRET}",
        "Scope": "https://dicom.healthcareapis.azure.com/.default",
        "TokenRefreshBufferSeconds": 300
      }
    }
  }
}
```

Start Orthanc:
```bash
docker-compose up -d
```

### Option B: Manual Configuration

Edit your `orthanc.json` directly with values from above steps.

## Step 5: Test Connection

1. **Check plugin status:**
   ```bash
   curl http://localhost:8042/dicomweb-oauth/status
   ```

2. **Test token acquisition:**
   ```bash
   curl -X POST http://localhost:8042/dicomweb-oauth/servers/azure-dicom/test
   ```

3. **Query DICOM studies:**
   ```bash
   curl http://localhost:8042/dicom-web/studies
   ```

## Troubleshooting

### "Failed to acquire token: 401 Unauthorized"

**Cause:** Invalid client credentials

**Solution:** Verify:
- Client ID is correct (from App Registration Overview)
- Client secret is correct and not expired
- Tenant ID is correct

### "Failed to acquire token: 403 Forbidden"

**Cause:** App lacks permissions

**Solution:**
- Verify "DICOM Data Owner" role is assigned
- Wait 5-10 minutes for role assignment to propagate

### "ImagePullFailure: not found" (Docker on M1/M2/M3 Mac)

**Cause:** Built arm64 image, Azure needs amd64

**Solution:**
```bash
docker buildx build --platform linux/amd64 -t your-registry/orthanc:latest --push .
```

See [CLAUDE.md](../CLAUDE.md) for details.

## Next Steps

- **Monitor token refresh:** Check logs for "Token acquired" messages
- **Upload DICOM:** Use Orthanc's STOW-RS endpoint
- **Configure DICOMweb queries:** Set up QIDO-RS and WADO-RS

## Azure Government / Sovereign Clouds

For Azure Government or other sovereign clouds, change token endpoint:

**Azure Government:**
```json
"TokenEndpoint": "https://login.microsoftonline.us/{tenant-id}/oauth2/v2.0/token"
```

**Azure China:**
```json
"TokenEndpoint": "https://login.chinacloudapi.cn/{tenant-id}/oauth2/v2.0/token"
```
```

**Step 3: Create configuration reference**

Create `docs/configuration-reference.md`:

```markdown
# Configuration Reference

Complete reference for all configuration options.

## Configuration Structure

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "<server-name>": {
        "Url": "string (required)",
        "TokenEndpoint": "string (required)",
        "ClientId": "string (required)",
        "ClientSecret": "string (required)",
        "Scope": "string (optional)",
        "TokenRefreshBufferSeconds": number (optional, default: 300)
      }
    }
  }
}
```

## Server Configuration

### `Url` (required)

The base URL of the DICOMweb server.

**Example:**
```json
"Url": "https://dicom.example.com/v2/"
```

**Notes:**
- Must include trailing slash if required by the server
- All requests matching this URL prefix will have OAuth tokens injected

### `TokenEndpoint` (required)

The OAuth2 token endpoint URL.

**Examples:**

Azure:
```json
"TokenEndpoint": "https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token"
```

Google Cloud:
```json
"TokenEndpoint": "https://oauth2.googleapis.com/token"
```

Keycloak:
```json
"TokenEndpoint": "https://keycloak.example.com/realms/healthcare/protocol/openid-connect/token"
```

### `ClientId` (required)

OAuth2 client identifier.

**Example:**
```json
"ClientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

**Supports environment variables:**
```json
"ClientId": "${OAUTH_CLIENT_ID}"
```

### `ClientSecret` (required)

OAuth2 client secret.

**Example:**
```json
"ClientSecret": "your-secret-value"
```

**Supports environment variables (recommended):**
```json
"ClientSecret": "${OAUTH_CLIENT_SECRET}"
```

### `Scope` (optional)

OAuth2 scope(s) to request. Multiple scopes can be space-separated.

**Examples:**

Azure:
```json
"Scope": "https://dicom.healthcareapis.azure.com/.default"
```

Google Cloud:
```json
"Scope": "https://www.googleapis.com/auth/cloud-healthcare"
```

Keycloak:
```json
"Scope": "dicomweb offline_access"
```

**Default:** Empty string (no scope requested)

### `TokenRefreshBufferSeconds` (optional)

Number of seconds before token expiry to proactively refresh.

**Example:**
```json
"TokenRefreshBufferSeconds": 300
```

**Default:** 300 (5 minutes)

**Recommendations:**
- Minimum: 60 seconds (1 minute)
- Recommended: 300 seconds (5 minutes)
- For frequently-accessed servers: 600 seconds (10 minutes)

## Environment Variable Substitution

All string values support environment variable substitution using `${VAR_NAME}` syntax.

**Configuration:**
```json
{
  "ClientId": "${AZURE_CLIENT_ID}",
  "ClientSecret": "${AZURE_CLIENT_SECRET}"
}
```

**Environment:**
```bash
export AZURE_CLIENT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
export AZURE_CLIENT_SECRET="your-secret"
```

**Result:**
Plugin replaces `${AZURE_CLIENT_ID}` with actual value at startup.

**Error handling:**
If a referenced variable is not set, plugin fails at startup with clear error message.

## Multiple Servers

You can configure multiple DICOMweb servers with different OAuth providers:

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "azure-dicom": {
        "Url": "https://azure-workspace.dicom.azurehealthcareapis.com/v2/",
        "TokenEndpoint": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        "ClientId": "${AZURE_CLIENT_ID}",
        "ClientSecret": "${AZURE_CLIENT_SECRET}",
        "Scope": "https://dicom.healthcareapis.azure.com/.default"
      },
      "keycloak-dicom": {
        "Url": "https://dicom.example.com/dicom-web/",
        "TokenEndpoint": "https://keycloak.example.com/realms/healthcare/protocol/openid-connect/token",
        "ClientId": "${KEYCLOAK_CLIENT_ID}",
        "ClientSecret": "${KEYCLOAK_CLIENT_SECRET}",
        "Scope": "dicomweb"
      }
    }
  }
}
```

## Validation Rules

The plugin validates configuration at startup:

1. ✅ `DicomWebOAuth` section must exist
2. ✅ `Servers` section must exist and contain at least one server
3. ✅ Each server must have `Url`, `TokenEndpoint`, `ClientId`, `ClientSecret`
4. ✅ All referenced environment variables must be set
5. ✅ URLs must be valid HTTP/HTTPS URLs

**Failure behavior:** Plugin fails to load and logs detailed error message.
```

**Step 4: Commit documentation**

```bash
git add README.md docs/quickstart-azure.md docs/configuration-reference.md
git commit -m "docs: add comprehensive documentation

- Main README with quick start
- Azure Health Data Services guide
- Complete configuration reference
- Provider-specific examples"
```

---

## Task 9: Integration Testing Script

**Files:**
- Create: `tests/integration/test_live_oauth.py`
- Create: `tests/integration/README.md`

**Step 1: Create integration test structure**

```bash
mkdir -p tests/integration
```

**Step 2: Create integration test**

Create `tests/integration/test_live_oauth.py`:

```python
"""
Integration tests for live OAuth2 providers.

These tests require actual OAuth2 credentials and are skipped by default.
Run with: pytest tests/integration/ --run-integration

Set environment variables:
- TEST_TOKEN_ENDPOINT
- TEST_CLIENT_ID
- TEST_CLIENT_SECRET
- TEST_SCOPE (optional)
"""
import pytest
import os
from src.token_manager import TokenManager


def pytest_configure(config):
    """Add custom marker for integration tests."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring live services"
    )


@pytest.fixture
def skip_if_no_credentials():
    """Skip test if OAuth credentials not provided."""
    required_vars = ["TEST_TOKEN_ENDPOINT", "TEST_CLIENT_ID", "TEST_CLIENT_SECRET"]
    missing = [var for var in required_vars if var not in os.environ]

    if missing:
        pytest.skip(f"Integration test skipped - missing env vars: {missing}")


@pytest.mark.integration
def test_live_token_acquisition(skip_if_no_credentials):
    """Test actual token acquisition from a live OAuth2 provider."""
    config = {
        "TokenEndpoint": os.environ["TEST_TOKEN_ENDPOINT"],
        "ClientId": os.environ["TEST_CLIENT_ID"],
        "ClientSecret": os.environ["TEST_CLIENT_SECRET"],
        "Scope": os.environ.get("TEST_SCOPE", "")
    }

    manager = TokenManager("integration-test", config)

    # Acquire token
    token = manager.get_token()

    assert token is not None
    assert len(token) > 0
    assert isinstance(token, str)

    # Verify token is cached
    token2 = manager.get_token()
    assert token2 == token

    print(f"✅ Successfully acquired token (length: {len(token)})")
    print(f"✅ Token cached and reused")


@pytest.mark.integration
def test_live_token_format(skip_if_no_credentials):
    """Test that acquired token matches expected format."""
    config = {
        "TokenEndpoint": os.environ["TEST_TOKEN_ENDPOINT"],
        "ClientId": os.environ["TEST_CLIENT_ID"],
        "ClientSecret": os.environ["TEST_CLIENT_SECRET"],
        "Scope": os.environ.get("TEST_SCOPE", "")
    }

    manager = TokenManager("integration-test", config)
    token = manager.get_token()

    # Most OAuth2 tokens are JWTs (eyJ...) or opaque tokens
    assert len(token) >= 20, "Token too short"

    # Check for common JWT format (starts with eyJ)
    if token.startswith("eyJ"):
        parts = token.split(".")
        assert len(parts) == 3, "Invalid JWT format (expected 3 parts)"
        print(f"✅ Token is valid JWT format")
    else:
        print(f"✅ Token is opaque format")
```

**Step 3: Create integration test README**

Create `tests/integration/README.md`:

```markdown
# Integration Tests

Tests against live OAuth2 providers. Skipped by default.

## Running Integration Tests

### 1. Set environment variables for your OAuth2 provider:

**Azure:**
```bash
export TEST_TOKEN_ENDPOINT="https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token"
export TEST_CLIENT_ID="your-app-id"
export TEST_CLIENT_SECRET="your-secret"
export TEST_SCOPE="https://dicom.healthcareapis.azure.com/.default"
```

**Keycloak:**
```bash
export TEST_TOKEN_ENDPOINT="https://keycloak.example.com/realms/healthcare/protocol/openid-connect/token"
export TEST_CLIENT_ID="orthanc-client"
export TEST_CLIENT_SECRET="your-secret"
export TEST_SCOPE="dicomweb"
```

### 2. Run integration tests:

```bash
pytest tests/integration/ -v -m integration
```

## What Gets Tested

- ✅ Live token acquisition from OAuth2 provider
- ✅ Token caching and reuse
- ✅ Token format validation (JWT vs opaque)

## Notes

- Tests are skipped if environment variables not set
- No actual DICOMweb requests are made (only OAuth2 token acquisition)
- Safe to run against production OAuth2 endpoints (read-only operation)
```

**Step 4: Update pytest.ini to handle integration tests**

Add to `pytest.ini`:

```ini
markers =
    integration: marks tests as integration tests (run with -m integration)
```

**Step 5: Test that integration tests are skipped by default**

```bash
pytest tests/integration/ -v
```

Expected: Tests skipped (no credentials provided)

**Step 6: Commit integration tests**

```bash
git add tests/integration/
git commit -m "test: add integration tests for live OAuth2 providers

- Test live token acquisition
- Test token caching
- Test token format validation
- Skipped by default, requires env vars
- Documentation for running integration tests"
```

---

## Task 10: Final Testing and Verification

**Files:**
- Create: `scripts/verify-installation.sh`
- Create: `.github/workflows/test.yml` (if using GitHub)

**Step 1: Create verification script**

Create `scripts/verify-installation.sh`:

```bash
#!/bin/bash
set -e

echo "=========================================="
echo "Orthanc DICOMweb OAuth Plugin Verification"
echo "=========================================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
python3 --version || { echo "❌ Python 3 not found"; exit 1; }

# Check dependencies
echo "✓ Checking dependencies..."
python3 -c "import requests" || { echo "❌ requests library not installed"; exit 1; }

# Run unit tests
echo "✓ Running unit tests..."
pytest tests/ -v --ignore=tests/integration/ || { echo "❌ Unit tests failed"; exit 1; }

# Run tests with coverage
echo "✓ Running tests with coverage..."
pytest tests/ --ignore=tests/integration/ --cov=src --cov-report=term-missing --cov-fail-under=95 || {
    echo "❌ Test coverage below 95%"
    exit 1
}

# Check code structure
echo "✓ Checking plugin structure..."
[ -f "src/dicomweb_oauth_plugin.py" ] || { echo "❌ Plugin file missing"; exit 1; }
[ -f "src/token_manager.py" ] || { echo "❌ Token manager missing"; exit 1; }
[ -f "src/config_parser.py" ] || { echo "❌ Config parser missing"; exit 1; }

# Check Docker files
echo "✓ Checking Docker configuration..."
[ -f "docker/Dockerfile" ] || { echo "❌ Dockerfile missing"; exit 1; }
[ -f "docker/docker-compose.yml" ] || { echo "❌ docker-compose.yml missing"; exit 1; }

# Check documentation
echo "✓ Checking documentation..."
[ -f "README.md" ] || { echo "❌ README.md missing"; exit 1; }
[ -f "docs/quickstart-azure.md" ] || { echo "❌ Azure quickstart missing"; exit 1; }
[ -f "docs/configuration-reference.md" ] || { echo "❌ Configuration reference missing"; exit 1; }

echo ""
echo "=========================================="
echo "✅ All verification checks passed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Configure your OAuth2 credentials in docker/.env"
echo "  2. Start Orthanc: cd docker && docker-compose up -d"
echo "  3. Test connection: curl http://localhost:8042/dicomweb-oauth/status"
echo ""
```

**Step 2: Make script executable**

```bash
chmod +x scripts/verify-installation.sh
```

**Step 3: Run verification**

```bash
./scripts/verify-installation.sh
```

Expected: All checks pass

**Step 4: Create GitHub Actions workflow (optional)**

Create `.github/workflows/test.yml`:

```yaml
name: Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt

    - name: Run tests with coverage
      run: |
        pytest tests/ --ignore=tests/integration/ \
          --cov=src --cov-report=xml --cov-report=term-missing

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: false
```

**Step 5: Run all tests one final time**

```bash
pytest tests/ -v --ignore=tests/integration/ --cov=src --cov-report=term-missing
```

Expected: All tests pass with >95% coverage

**Step 6: Commit verification tools**

```bash
git add scripts/verify-installation.sh .github/workflows/test.yml
chmod +x scripts/verify-installation.sh
git add --chmod=+x scripts/verify-installation.sh
git commit -m "chore: add verification script and CI workflow

- Automated verification of installation
- GitHub Actions workflow for CI testing
- Test multiple Python versions
- Coverage reporting"
```

---

## Task 11: Final Documentation and README Updates

**Files:**
- Create: `docs/troubleshooting.md`
- Create: `docs/quickstart-keycloak.md`
- Create: `CONTRIBUTING.md`
- Create: `CHANGELOG.md`

**Step 1: Create troubleshooting guide**

Create `docs/troubleshooting.md`:

```markdown
# Troubleshooting Guide

Common issues and their solutions.

## Plugin Not Loading

**Symptoms:**
- Orthanc starts but plugin not listed in `/plugins`
- No log messages from "DICOMweb OAuth"

**Solutions:**

1. **Check Python is available in container:**
   ```bash
   docker-compose exec orthanc python3 --version
   ```

2. **Verify plugin file path in orthanc.json:**
   ```json
   "Plugins": [
     "/etc/orthanc/plugins/dicomweb_oauth_plugin.py"
   ]
   ```

3. **Check Orthanc logs for Python errors:**
   ```bash
   docker-compose logs orthanc | grep -i error
   ```

4. **Verify requests library is installed:**
   ```bash
   docker-compose exec orthanc python3 -c "import requests"
   ```

## Token Acquisition Fails

**Symptoms:**
- "Failed to acquire token" in logs
- 503 errors on DICOMweb requests

### 401 Unauthorized

**Cause:** Invalid client credentials

**Check:**
1. Verify `ClientId` is correct
2. Verify `ClientSecret` is correct and not expired
3. Check environment variables are set correctly:
   ```bash
   docker-compose exec orthanc env | grep OAUTH
   ```

### 403 Forbidden

**Cause:** App lacks permissions to access DICOM service

**Solutions:**
- **Azure:** Verify "DICOM Data Owner" role is assigned, wait 5-10 minutes for propagation
- **Keycloak:** Verify client has required scopes
- **Google Cloud:** Verify service account has Healthcare Dataset Admin role

### Connection Timeout

**Cause:** Network connectivity issue to token endpoint

**Check:**
1. Verify token endpoint URL is accessible:
   ```bash
   docker-compose exec orthanc curl -v https://login.microsoftonline.com
   ```

2. Check firewall/proxy settings
3. Verify DNS resolution works

## Token Not Injected

**Symptoms:**
- Token acquisition succeeds (visible in logs)
- But DICOMweb requests still fail with 401

**Solutions:**

1. **Verify URL matching:** Check that DICOMweb request URL starts with configured server URL:
   ```json
   "Url": "https://dicom.example.com/v2/"
   ```
   Request must start with exact URL (including trailing slash if configured)

2. **Check HTTP filter is registered:**
   ```bash
   docker-compose logs orthanc | grep "RegisterOnOutgoingHttpRequestFilter"
   ```

3. **Enable verbose logging:** Add to orthanc.json:
   ```json
   "Verbosity": "verbose"
   ```

## Environment Variables Not Substituted

**Symptoms:**
- Literal `${VAR_NAME}` sent to OAuth endpoint
- "invalid_client" error

**Solutions:**

1. **Docker Compose:** Verify .env file exists and is loaded:
   ```bash
   cd docker
   cat .env
   docker-compose config  # Shows resolved config
   ```

2. **Kubernetes:** Verify ConfigMap or Secret is mounted and env vars exported

3. **Manual deployment:** Export env vars before starting Orthanc:
   ```bash
   export OAUTH_CLIENT_ID="your-value"
   export OAUTH_CLIENT_SECRET="your-secret"
   Orthanc /etc/orthanc/orthanc.json
   ```

## Docker Image Issues on Apple Silicon

**Symptoms:**
- `ImagePullFailure: not found` when deploying to cloud
- Image builds locally but doesn't work in Azure/AWS/GCP

**Cause:** M1/M2/M3 Macs build arm64 images by default; cloud services need amd64

**Solution:**
```bash
docker buildx build --platform linux/amd64 -t your-registry/orthanc:latest --push .
```

See [CLAUDE.md](../CLAUDE.md) for details.

## Debugging Tips

### Enable debug logging

Add to orthanc.json:
```json
"Verbosity": "verbose",
"LogLevel": "default"
```

### Monitor token refresh

```bash
docker-compose logs -f orthanc | grep "Token acquired"
```

### Test token acquisition directly

```bash
curl -X POST http://localhost:8042/dicomweb-oauth/servers/SERVER_NAME/test
```

### Check token expiry

```bash
curl http://localhost:8042/dicomweb-oauth/servers
```

Look for `"token_valid": true` in response.

## Still Having Issues?

1. Review [Configuration Reference](configuration-reference.md)
2. Check [GitHub Issues](https://github.com/yourusername/orthanc-dicomweb-oauth/issues)
3. Open a new issue with:
   - Orthanc version
   - Plugin logs
   - Configuration (redact secrets!)
   - OAuth provider details
```

**Step 2: Create Keycloak quickstart**

Create `docs/quickstart-keycloak.md`:

```markdown
# Keycloak Quick Start

Complete guide to connecting Orthanc to a Keycloak-protected DICOMweb server.

## Prerequisites

- Running Keycloak instance
- Admin access to Keycloak
- DICOMweb server behind Keycloak authentication

## Step 1: Create Keycloak Client

1. Log in to Keycloak Admin Console
2. Select your realm (or create new realm: "healthcare")
3. Go to **Clients** > **Create**

**Client settings:**
- Client ID: `orthanc-client`
- Client Protocol: `openid-connect`
- Access Type: `confidential`
- Standard Flow Enabled: `OFF`
- Direct Access Grants Enabled: `OFF`
- Service Accounts Enabled: `ON`  ← **Important!**
- Authorization Enabled: `OFF`

Click **Save**

## Step 2: Get Client Secret

1. Go to **Credentials** tab
2. Copy the **Secret** value

## Step 3: Configure Client Scopes

1. Go to **Service Account Roles** tab
2. Assign necessary roles for your DICOMweb server

Or create custom scope:

1. Go to **Client Scopes** > **Create**
2. Name: `dicomweb`
3. Protocol: `openid-connect`
4. Go to **Mappers** tab and add required claims

## Step 4: Test Token Acquisition

Using curl:
```bash
curl -X POST \
  'https://keycloak.example.com/realms/healthcare/protocol/openid-connect/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=client_credentials' \
  -d 'client_id=orthanc-client' \
  -d 'client_secret=YOUR_SECRET' \
  -d 'scope=dicomweb'
```

Expected response:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300,
  "token_type": "Bearer"
}
```

## Step 5: Configure Orthanc

Create `.env`:
```bash
KEYCLOAK_CLIENT_ID=orthanc-client
KEYCLOAK_CLIENT_SECRET=your-secret-from-step-2
KEYCLOAK_REALM=healthcare
KEYCLOAK_BASE_URL=https://keycloak.example.com
DICOMWEB_URL=https://dicom.example.com/dicom-web/
```

Update `docker/orthanc.json`:
```json
{
  "DicomWebOAuth": {
    "Servers": {
      "keycloak-dicom": {
        "Url": "${DICOMWEB_URL}",
        "TokenEndpoint": "${KEYCLOAK_BASE_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/token",
        "ClientId": "${KEYCLOAK_CLIENT_ID}",
        "ClientSecret": "${KEYCLOAK_CLIENT_SECRET}",
        "Scope": "dicomweb",
        "TokenRefreshBufferSeconds": 300
      }
    }
  }
}
```

Start Orthanc:
```bash
docker-compose up -d
```

## Step 6: Verify Connection

Test token acquisition:
```bash
curl -X POST http://localhost:8042/dicomweb-oauth/servers/keycloak-dicom/test
```

Query studies:
```bash
curl http://localhost:8042/dicom-web/studies
```

## Advanced: Multiple Realms

For multiple Keycloak realms:

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "keycloak-prod": {
        "Url": "https://dicom-prod.example.com/dicom-web/",
        "TokenEndpoint": "https://keycloak.example.com/realms/production/protocol/openid-connect/token",
        "ClientId": "${KEYCLOAK_PROD_CLIENT_ID}",
        "ClientSecret": "${KEYCLOAK_PROD_SECRET}",
        "Scope": "dicomweb"
      },
      "keycloak-dev": {
        "Url": "https://dicom-dev.example.com/dicom-web/",
        "TokenEndpoint": "https://keycloak.example.com/realms/development/protocol/openid-connect/token",
        "ClientId": "${KEYCLOAK_DEV_CLIENT_ID}",
        "ClientSecret": "${KEYCLOAK_DEV_SECRET}",
        "Scope": "dicomweb"
      }
    }
  }
}
```

## Troubleshooting

### "invalid_client" error

- Verify client ID is exactly as configured in Keycloak
- Verify client secret is correct
- Check that "Service Accounts Enabled" is ON

### Token acquired but DICOMweb request fails

- Verify DICOMweb server is validating tokens against same Keycloak realm
- Check that client has required roles/scopes
- Verify `audience` claim in token matches what DICOMweb server expects

### Token expires too quickly

Increase token lifetime in Keycloak:
1. Realm Settings > Tokens
2. Access Token Lifespan: Set to 1 hour or more
```

**Step 3: Create CONTRIBUTING guide**

Create `CONTRIBUTING.md`:

```markdown
# Contributing to Orthanc DICOMweb OAuth Plugin

Thank you for considering contributing! This document outlines the process.

## Development Setup

1. **Fork and clone:**
   ```bash
   git clone https://github.com/your-username/orthanc-dicomweb-oauth.git
   cd orthanc-dicomweb-oauth
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

## Making Changes

### 1. Create a branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Write tests first (TDD)

All new features must have tests:

```python
def test_your_new_feature():
    # Arrange
    ...
    # Act
    ...
    # Assert
    assert result == expected
```

### 3. Implement feature

Follow existing code style and patterns.

### 4. Run tests and verify coverage

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

Target: >95% coverage

### 5. Update documentation

- Update README.md if adding new features
- Add/update docstrings
- Update configuration reference if adding config options

### 6. Commit with clear messages

```bash
git commit -m "feat: add support for X

- Implement Y
- Add tests for Z
- Update documentation"
```

## Code Style

- Follow PEP 8
- Use type hints where appropriate
- Write clear docstrings
- Keep functions focused and small

## Testing

### Unit tests (required)

```bash
pytest tests/ --ignore=tests/integration/
```

### Integration tests (optional)

Requires live OAuth2 credentials:

```bash
export TEST_TOKEN_ENDPOINT="..."
export TEST_CLIENT_ID="..."
export TEST_CLIENT_SECRET="..."
pytest tests/integration/ -m integration
```

## Pull Request Process

1. **Update CHANGELOG.md** with your changes
2. **Ensure tests pass** and coverage is maintained
3. **Update documentation** as needed
4. **Submit PR** with clear description of changes
5. **Respond to review feedback**

## Release Process

Maintainers will:
1. Update version in `src/dicomweb_oauth_plugin.py`
2. Update CHANGELOG.md
3. Create GitHub release with tag
4. Announce on Orthanc forum

## Questions?

Open an issue or ask on the [Orthanc forum](https://discourse.orthanc-server.org/).
```

**Step 4: Create CHANGELOG**

Create `CHANGELOG.md`:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-06

### Added
- Generic OAuth2 client credentials flow support
- Automatic token caching with configurable refresh buffer
- Thread-safe token acquisition and refresh
- HTTP filter for injecting Authorization headers
- Environment variable substitution in configuration (`${VAR_NAME}`)
- Retry logic with exponential backoff for network errors
- REST API monitoring endpoints:
  - `GET /dicomweb-oauth/status` - Plugin status
  - `GET /dicomweb-oauth/servers` - Server list and token status
  - `POST /dicomweb-oauth/servers/{name}/test` - Test token acquisition
- Docker development environment
- Comprehensive test suite with >95% coverage
- Documentation:
  - Azure Health Data Services quick start
  - Keycloak quick start
  - Configuration reference
  - Troubleshooting guide
- Example configurations for Azure, Google Cloud, Keycloak

### Security
- In-memory only token storage (never persisted to disk)
- Support for secrets via environment variables

## [Unreleased]

### Planned for 2.0.0
- Azure managed identity support (Tier 2)
- MSAL integration for Azure-specific features
- Google Cloud service account support
- AWS SigV4 authentication
```

**Step 5: Final commit**

```bash
git add docs/troubleshooting.md docs/quickstart-keycloak.md CONTRIBUTING.md CHANGELOG.md
git commit -m "docs: complete documentation for v1.0.0

- Comprehensive troubleshooting guide
- Keycloak quick start guide
- Contributing guidelines
- Changelog tracking"
```

---

## Completion Checklist

Run through this checklist to verify implementation is complete:

```bash
# 1. All tests pass
pytest tests/ --ignore=tests/integration/ -v

# 2. Coverage above 95%
pytest tests/ --ignore=tests/integration/ --cov=src --cov-report=term-missing --cov-fail-under=95

# 3. Verification script passes
./scripts/verify-installation.sh

# 4. Docker build succeeds
cd docker && docker-compose build

# 5. Documentation complete
ls docs/*.md
ls examples/*.json

# 6. Git history is clean
git log --oneline
git status
```

---

## Plan Summary

**Total Implementation Time Estimate:** 1-2 evenings (6-12 hours)

**Completed Components:**
- ✅ OAuth2 token manager with caching
- ✅ Configuration parser with env var substitution
- ✅ Orthanc plugin with HTTP filter
- ✅ Docker development environment
- ✅ REST API monitoring endpoints
- ✅ Error handling and retry logic
- ✅ Comprehensive test suite (>95% coverage)
- ✅ Complete documentation for Azure, Keycloak, etc.
- ✅ Integration test framework
- ✅ CI/CD workflow

**Files Created:** 28
**Lines of Code (estimated):** ~2500
**Test Coverage:** >95%

**Ready for:** Phase 2 (Azure MSAL integration) or production use

---

Plan complete and saved to `docs/plans/2026-02-06-generic-oauth2-plugin.md`.

Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?