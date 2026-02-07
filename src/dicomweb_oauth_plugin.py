"""
Orthanc DICOMweb OAuth2 Plugin

Generic OAuth2/OIDC token management plugin for Orthanc's DICOMweb connections.
Automatically acquires, caches, and refreshes bearer tokens for any OAuth2-protected
DICOMweb endpoint.
"""
import json
import logging
from typing import Dict, Optional

try:
    import orthanc
    ORTHANC_AVAILABLE = True
except ImportError:
    ORTHANC_AVAILABLE = False
    orthanc = None

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


# Plugin registration - only run when orthanc module is available
if ORTHANC_AVAILABLE and orthanc is not None:
    try:
        logger.info("Registering DICOMweb OAuth plugin with Orthanc")
        initialize_plugin()
        orthanc.RegisterOnOutgoingHttpRequestFilter(on_outgoing_http_request)
        logger.info("DICOMweb OAuth plugin registered successfully")
    except Exception as e:
        logger.error(f"Failed to register plugin: {e}")
        raise
