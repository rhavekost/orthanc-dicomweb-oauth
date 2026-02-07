"""
Orthanc DICOMweb OAuth2 Plugin

Generic OAuth2/OIDC token management plugin for Orthanc's DICOMweb connections.
Automatically acquires, caches, and refreshes bearer tokens for any OAuth2-protected
DICOMweb endpoint.
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

try:
    import orthanc

    _ORTHANC_AVAILABLE = True
except ImportError:
    _ORTHANC_AVAILABLE = False
    orthanc = None

from src.config_parser import ConfigError, ConfigParser
from src.plugin_context import PluginContext
from src.token_manager import TokenAcquisitionError, TokenManager

# Plugin version
__version__ = "1.0.0"

# API versioning
try:
    from importlib.metadata import version

    PLUGIN_VERSION = version("orthanc-dicomweb-oauth")
except Exception:
    # Fallback if package not installed (development/testing)
    PLUGIN_VERSION = __version__

API_VERSION = "2.0"  # Major.Minor only

# Global context instance
_plugin_context: Optional[PluginContext] = None

logger = logging.getLogger(__name__)


def initialize_plugin(
    orthanc_module: Any = None, context: Optional[PluginContext] = None
) -> None:
    """
    Initialize the DICOMweb OAuth plugin.

    Args:
        orthanc_module: Orthanc module (for testing, defaults to global orthanc)
        context: Plugin context (for testing, creates new if None)
    """
    global _plugin_context

    if orthanc_module is None:
        orthanc_module = orthanc

    # Create or use provided context (allows dependency injection in tests)
    if context is None:
        context = PluginContext()

    _plugin_context = context

    logger.info("Initializing DICOMweb OAuth plugin")

    try:
        # Load configuration
        config = orthanc_module.GetConfiguration()
        parser = ConfigParser(config)
        servers = parser.get_servers()

        # Initialize token manager for each configured server
        for server_name, server_config in servers.items():
            logger.info(f"Configuring OAuth for server: {server_name}")

            manager = TokenManager(server_name, server_config)
            context.register_token_manager(
                server_name=server_name, manager=manager, url=server_config["Url"]
            )

            logger.info(
                f"Server '{server_name}' configured with URL: {server_config['Url']}"
            )

        logger.info(f"DICOMweb OAuth plugin initialized with {len(servers)} server(s)")

    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize plugin: {e}")
        raise


def get_plugin_context() -> PluginContext:
    """Get the plugin context (for use in callbacks)."""
    if _plugin_context is None:
        raise RuntimeError("Plugin not initialized")
    return _plugin_context


def on_outgoing_http_request(
    uri: str,
    method: str,
    headers: Dict[str, str],
    get_params: Dict[str, str],
    body: bytes,
) -> Optional[Dict]:
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
    context = get_plugin_context()

    # Find which server this request is for
    server_name = context.find_server_for_uri(uri)

    if server_name is None:
        # Not a configured OAuth server, let it pass through
        return None

    logger.debug(f"Injecting OAuth token for server '{server_name}'")

    try:
        # Get valid token
        token_manager = context.get_token_manager(server_name)
        if token_manager is None:
            logger.error(f"No token manager for server '{server_name}'")
            return None

        token = token_manager.get_token()

        # Inject Authorization header
        headers["Authorization"] = f"Bearer {token}"

        # Return modified request
        return {
            "headers": headers,
            "method": method,
            "uri": uri,
            "get_params": get_params,
            "body": body,
        }

    except TokenAcquisitionError as e:
        logger.error(f"Failed to acquire token for '{server_name}': {e}")
        # Return error response
        return {
            "status": 503,
            "body": json.dumps(
                {
                    "error": "OAuth token acquisition failed",
                    "server": server_name,
                    "details": str(e),
                }
            ),
        }


def create_api_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create standardized API response with version information.

    Args:
        data: Response data payload

    Returns:
        Response dictionary with version headers and data
    """
    from datetime import timezone

    return {
        "plugin_version": PLUGIN_VERSION,
        "api_version": API_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "data": data,
    }


def handle_rest_api_status(output: Any, uri: str, **request: Any) -> None:
    """
    REST API endpoint: Plugin status check.

    Returns plugin health, version, and basic metrics.

    GET /dicomweb-oauth/status

    Response:
        {
            "plugin_version": "2.0.0",
            "api_version": "2.0",
            "timestamp": "2026-02-07T10:30:00Z",
            "data": {
                "status": "healthy",
                "token_managers": 1,
                "servers_configured": 1
            }
        }
    """
    try:
        context = get_plugin_context()

        data = {
            "status": "healthy",
            "token_managers": len(context.token_managers),
            "servers_configured": len(context.server_urls),
        }

        response = create_api_response(data)
        output.AnswerBuffer(json.dumps(response, indent=2), "application/json")

    except Exception as e:
        logger.error(f"Status endpoint failed: {type(e).__name__}: {e}")
        error_response = create_api_response({"status": "error", "error": str(e)})
        output.AnswerBuffer(json.dumps(error_response), "application/json")


def handle_rest_api_servers(output: Any, uri: str, **request: Any) -> None:
    """
    REST API endpoint: List configured servers.

    Returns list of configured OAuth servers and their token status.

    GET /dicomweb-oauth/servers

    Response:
        {
            "plugin_version": "2.0.0",
            "api_version": "2.0",
            "timestamp": "2026-02-07T10:30:00Z",
            "data": {
                "servers": [...]
            }
        }
    """
    try:
        context = get_plugin_context()

        servers = []
        for server_name, token_manager in context.token_managers.items():
            server_info = {
                "name": server_name,
                "url": context.get_server_url(server_name),
                "token_endpoint": token_manager.token_endpoint,
                "has_cached_token": token_manager._cached_token is not None,
                "token_valid": token_manager._is_token_valid()
                if token_manager._cached_token
                else False,
            }
            servers.append(server_info)

        response = create_api_response({"servers": servers})
        output.AnswerBuffer(json.dumps(response, indent=2), "application/json")

    except Exception as e:
        logger.error(f"Servers endpoint failed: {type(e).__name__}: {e}")
        error_response = create_api_response({"error": str(e)})
        output.AnswerBuffer(json.dumps(error_response), "application/json")


def handle_rest_api_test_server(output: Any, uri: str, **request: Any) -> None:
    """
    POST /dicomweb-oauth/servers/{name}/test

    Test token acquisition for a specific server.
    """
    context = get_plugin_context()

    # Extract server name from URI
    parts = uri.split("/")
    if len(parts) < 4:
        output.AnswerBuffer(
            json.dumps({"error": "Server name not specified"}),
            "application/json",
            status=400,
        )
        return

    server_name = parts[-2]

    if server_name not in context.token_managers:
        output.AnswerBuffer(
            json.dumps({"error": f"Server '{server_name}' not configured"}),
            "application/json",
            status=404,
        )
        return

    try:
        token_manager = context.get_token_manager(server_name)
        if token_manager is None:
            output.AnswerBuffer(
                json.dumps({"error": f"Server '{server_name}' not configured"}),
                "application/json",
                status=404,
            )
            return

        token = token_manager.get_token()

        result = {
            "server": server_name,
            "status": "success",
            "token_acquired": True,
            "has_token": token is not None,
        }

        output.AnswerBuffer(json.dumps(result, indent=2), "application/json")

    except TokenAcquisitionError as e:
        result = {"server": server_name, "status": "error", "error": str(e)}
        output.AnswerBuffer(
            json.dumps(result, indent=2), "application/json", status=503
        )


# Orthanc plugin entry point
def OnChange(changeType: int, level: int, resource: str) -> None:
    """Orthanc change callback (not used, but required by plugin API)."""
    pass


def OnIncomingHttpRequest(
    method: str, uri: str, ip: str, username: str, headers: Dict[str, str]
) -> None:
    """Orthanc incoming HTTP request callback (not used for this plugin)."""
    pass


# Plugin registration - only run when orthanc module is available
if _ORTHANC_AVAILABLE and orthanc is not None:
    try:
        logger.info("Registering DICOMweb OAuth plugin with Orthanc")
        initialize_plugin()
        orthanc.RegisterOnOutgoingHttpRequestFilter(on_outgoing_http_request)

        # Register REST API endpoints
        logger.info("Registering REST API endpoints")
        orthanc.RegisterRestCallback("/dicomweb-oauth/status", handle_rest_api_status)
        orthanc.RegisterRestCallback("/dicomweb-oauth/servers", handle_rest_api_servers)
        orthanc.RegisterRestCallback(
            "/dicomweb-oauth/servers/(.*)/test", handle_rest_api_test_server
        )

        logger.info("DICOMweb OAuth plugin registered successfully")
    except Exception as e:
        logger.error(f"Failed to register plugin: {e}")
        raise
