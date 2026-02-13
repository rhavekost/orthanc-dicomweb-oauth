"""
Orthanc DICOMweb OAuth2 Plugin.

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

try:
    from flask import Flask, jsonify, request

    _FLASK_AVAILABLE = True
except ImportError:
    _FLASK_AVAILABLE = False
    Flask = None
    jsonify = None
    request = None

from src.config_parser import ConfigError, ConfigParser
from src.metrics import get_metrics_text
from src.plugin_context import PluginContext
from src.rate_limiter import RateLimiter, RateLimitExceeded
from src.structured_logger import structured_logger
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

logger = logging.getLogger(__name__)


def initialize_plugin(
    orthanc_module: Any = None, context: Optional[PluginContext] = None
) -> None:
    """
    Initialize the DICOMweb OAuth plugin.

    Args:
        orthanc_module: Orthanc module (for testing, defaults to global orthanc)
        context: Plugin context (for testing, uses singleton if None)
    """
    if orthanc_module is None:
        orthanc_module = orthanc

    # Use singleton pattern instead of global
    if context is None:
        context = PluginContext.get_instance()

    logger.info("Initializing DICOMweb OAuth plugin")

    try:
        # Load configuration (GetConfiguration returns JSON string)
        config_str = orthanc_module.GetConfiguration()
        config = json.loads(config_str)
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
    """Get the plugin context (singleton)."""
    return PluginContext.get_instance()


def on_outgoing_http_request(
    uri: str,
    method: str,
    headers: Dict[str, str],
    get_params: Dict[str, str],
    body: bytes,
) -> Optional[Dict[str, Any]]:
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
    server_name = context.find_server_for_url(uri)

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


def handle_rest_api_status(output: Any, uri: str, **_request: Any) -> None:
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


def handle_rest_api_servers(output: Any, uri: str, **_request: Any) -> None:
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
                "has_cached_token": token_manager._encrypted_cached_token is not None,
                "token_valid": token_manager._is_token_valid()
                if token_manager._encrypted_cached_token
                else False,
            }
            servers.append(server_info)

        response = create_api_response({"servers": servers})
        output.AnswerBuffer(json.dumps(response, indent=2), "application/json")

    except Exception as e:
        logger.error(f"Servers endpoint failed: {type(e).__name__}: {e}")
        error_response = create_api_response({"error": str(e)})
        output.AnswerBuffer(json.dumps(error_response), "application/json")


def handle_rest_api_test_server(output: Any, uri: str, **_request: Any) -> None:
    """
    POST /dicomweb-oauth/servers/{name}/test.

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


def metrics_endpoint(output: Any, uri: str, **_request: Any) -> None:
    """
    REST API endpoint: Prometheus metrics.

    Returns metrics in Prometheus text format for monitoring.

    GET /dicomweb-oauth/metrics

    Response:
        Prometheus text format (Content-Type: text/plain; version=0.0.4)
    """
    try:
        metrics_text = get_metrics_text()
        output.AnswerBuffer(metrics_text, "text/plain; version=0.0.4")
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        error_message = f"Error generating metrics: {e}"
        output.AnswerBuffer(error_message, "text/plain", status=500)


# Flask app for testing with rate limiting
def create_flask_app(
    servers_config: Dict[str, Any],
    rate_limit_requests: int = 10,
    rate_limit_window: int = 60,
) -> Any:
    """
    Create Flask application with rate limiting for testing.

    Args:
        servers_config: Server configurations
        rate_limit_requests: Max requests per window
        rate_limit_window: Time window in seconds

    Returns:
        Configured Flask application
    """
    if not _FLASK_AVAILABLE:
        raise ImportError("Flask is required for create_flask_app")

    app = Flask(__name__)

    # Initialize rate limiter
    app.rate_limiter = RateLimiter(
        max_requests=rate_limit_requests, window_seconds=rate_limit_window
    )

    structured_logger.info(
        "Rate limiting enabled",
        max_requests=rate_limit_requests,
        window_seconds=rate_limit_window,
    )

    # Initialize plugin context with test configuration
    context = PluginContext.get_instance()
    context.token_managers.clear()
    context.server_urls.clear()

    for server_name, server_config in servers_config.items():
        if "TokenEndpoint" in server_config:
            manager = TokenManager(server_name, server_config)
            context.register_token_manager(
                server_name=server_name,
                manager=manager,
                url=server_config.get("Url", f"https://{server_name}"),
            )

    # Rate limiting middleware
    @app.before_request  # type: ignore[misc]
    def check_rate_limit() -> Any:
        """Check rate limit before processing request."""
        # Use remote address as rate limit key
        client_key = request.remote_addr or "unknown"

        try:
            app.rate_limiter.check_rate_limit(client_key)
        except RateLimitExceeded as e:
            # Log security event
            structured_logger.security_event(
                event_type="rate_limit_exceeded",
                operation="rate_limit",
                client_ip=client_key,
                endpoint=request.endpoint,
                method=request.method,
                max_requests=e.max_requests,
                window_seconds=e.window_seconds,
            )

            return (
                jsonify(
                    {
                        "error": str(e),
                        "max_requests": e.max_requests,
                        "window_seconds": e.window_seconds,
                    }
                ),
                429,
            )

        return None

    # Register routes
    @app.route("/dicomweb-oauth/status", methods=["GET"])  # type: ignore[misc]
    def handle_status() -> Any:
        """Handle status endpoint."""
        try:
            data = {
                "status": "healthy",
                "token_managers": len(context.token_managers),
                "servers_configured": len(context.server_urls),
            }
            response = create_api_response(data)
            return jsonify(response)
        except Exception as e:
            error_response = create_api_response({"status": "error", "error": str(e)})
            return jsonify(error_response)

    @app.route(  # type: ignore[misc]
        "/dicomweb-oauth/servers/<name>/test", methods=["POST"]
    )
    def handle_test(name: str) -> Any:
        """Handle test endpoint."""
        if name not in context.token_managers:
            return (
                jsonify({"error": f"Server '{name}' not configured"}),
                404,
            )

        try:
            token_manager = context.get_token_manager(name)
            if token_manager is None:
                return jsonify({"error": f"Server '{name}' not configured"}), 404

            token = token_manager.get_token()

            result = {
                "server": name,
                "status": "success",
                "token_acquired": True,
                "has_token": token is not None,
            }

            return jsonify(result)

        except TokenAcquisitionError as e:
            result = {"server": name, "status": "error", "error": str(e)}
            return jsonify(result), 503

    return app


# Orthanc plugin entry point
def OnChange(_changeType: int, level: int, _resource: str) -> None:
    """Orthanc change callback (not used, but required by plugin API)."""
    pass


def OnIncomingHttpRequest(
    method: str, uri: str, _ip: str, _username: str, headers: Dict[str, str]
) -> None:
    """Orthanc incoming HTTP request callback (not used for this plugin)."""
    pass


# Plugin registration - only run when orthanc module is available
if _ORTHANC_AVAILABLE and orthanc is not None:
    try:
        logger.info("Registering DICOMweb OAuth plugin with Orthanc")
        initialize_plugin()

        # Register HTTP request filter only if available (Orthanc SDK >= 1.12.1)
        if hasattr(orthanc, "RegisterOnOutgoingHttpRequestFilter"):
            logger.info("Registering outgoing HTTP request filter")
            orthanc.RegisterOnOutgoingHttpRequestFilter(on_outgoing_http_request)
        else:
            logger.warning(
                "RegisterOnOutgoingHttpRequestFilter not available - "
                "automatic OAuth token injection will not work. "
                "Please upgrade to Orthanc SDK >= 1.12.1"
            )

        # Register REST API endpoints
        logger.info("Registering REST API endpoints")
        orthanc.RegisterRestCallback("/dicomweb-oauth/status", handle_rest_api_status)
        orthanc.RegisterRestCallback("/dicomweb-oauth/servers", handle_rest_api_servers)
        orthanc.RegisterRestCallback(
            "/dicomweb-oauth/servers/(.*)/test", handle_rest_api_test_server
        )
        orthanc.RegisterRestCallback("/dicomweb-oauth/metrics", metrics_endpoint)

        logger.info(
            "DICOMweb OAuth plugin registered successfully "
            "(including /dicomweb-oauth/metrics)"
        )
    except Exception as e:
        logger.error(f"Failed to register plugin: {e}")
        raise
