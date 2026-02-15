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
        # Load configuration (string in Orthanc, dict in tests)
        config_data = orthanc_module.GetConfiguration()
        config = (
            json.loads(config_data) if isinstance(config_data, str) else config_data
        )
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


def handle_rest_api_stow(output: Any, uri: str, **request: Any) -> None:
    """
    POST /dicomweb-oauth/servers/{name}/stow

    Proxy STOW-RS requests with automatic OAuth token injection.
    Acts as a transparent proxy between DICOMweb plugin and remote DICOM server.

    Request body: Same as Orthanc's native STOW-RS endpoint
    {
        "Resources": ["orthanc-id-1", "orthanc-id-2"],
        "Synchronous": true/false,
        "Priority": 0
    }
    """
    print(f"DEBUG: handle_rest_api_stow CALLED! URI: {uri}", flush=True)
    import orthanc

    try:
        context = get_plugin_context()
        print("DEBUG: Got plugin context", flush=True)
        print(f"DEBUG: Request headers: {request.get('headers', {})}", flush=True)
        body_len = len(request.get("body", b"")) if request.get("body") else 0
        print(f"DEBUG: Request body length: {body_len}", flush=True)

        # Extract server name from URI: /dicomweb-oauth/servers/{name}/stow
        parts = uri.split("/")
        if len(parts) < 5:
            output.AnswerBuffer(
                json.dumps({"error": "Server name not specified"}), "application/json"
            )
            return

        server_name = parts[3]

        # Get token manager for this server
        token_manager = context.get_token_manager(server_name)
        if not token_manager:
            output.AnswerBuffer(
                json.dumps({"error": f"Server '{server_name}' not configured"}),
                "application/json",
            )
            return

        # Get OAuth token
        try:
            token = token_manager.get_token()
        except TokenAcquisitionError as e:
            logger.error(f"Failed to acquire token for '{server_name}': {e}")
            output.AnswerBuffer(
                json.dumps(
                    {"error": "OAuth token acquisition failed", "details": str(e)}
                ),
                "application/json",
            )
            return

        # Check if request is multipart/related (DICOMweb plugin sends DICOM directly)
        # or JSON (API calls send resource IDs)
        content_type = request.get("headers", {}).get("content-type", "")
        body = request.get("body", b"")

        # Get server URL
        server_url = context.get_server_url(server_name)
        if not server_url:
            output.AnswerBuffer(
                json.dumps({"error": f"Server URL not found for '{server_name}'"}),
                "application/json",
            )
            return

        # Build STOW-RS URL (append /studies for STOW-RS endpoint)
        stow_url = f"{server_url.rstrip('/')}/studies"

        import requests

        if "multipart/related" in content_type:
            # DICOMweb plugin is sending pre-formatted multipart DICOM data
            # Forward it directly to Azure with OAuth token
            logger.info(
                f"Forwarding multipart DICOM data ({len(body)} bytes) to {stow_url}"
            )

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": content_type,
                "Accept": "application/dicom+json",
            }
        else:
            # JSON request with resource IDs - build multipart ourselves
            try:
                body_str = body.decode("utf-8") if isinstance(body, bytes) else body
                request_data = json.loads(body_str) if body_str else {}
                resources = request_data.get("Resources", [])
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                output.AnswerBuffer(
                    json.dumps({"error": f"Invalid request body: {type(e).__name__}"}),
                    "application/json",
                )
                return

            if not resources:
                output.AnswerBuffer(
                    json.dumps({"error": "No resources specified"}), "application/json"
                )
                return

            logger.info(f"Building multipart from {len(resources)} resources")

            import uuid

            boundary = uuid.uuid4().hex

            # Build multipart message
            multipart_data = []
            for resource_id in resources:
                try:
                    dicom_data = orthanc.RestApiGet(f"/instances/{resource_id}/file")
                    part_header = f"--{boundary}\r\n"
                    part_header += "Content-Type: application/dicom\r\n\r\n"
                    multipart_data.append(part_header.encode("utf-8"))
                    multipart_data.append(dicom_data)
                    multipart_data.append(b"\r\n")
                except Exception as e:
                    logger.error(f"Failed to get DICOM file for {resource_id}: {e}")
                    output.AnswerBuffer(
                        json.dumps({"error": f"Failed to get DICOM file: {str(e)}"}),
                        "application/json",
                    )
                    return

            multipart_data.append(f"--{boundary}--\r\n".encode("utf-8"))
            body = b"".join(multipart_data)

            content_type_value = (
                f'multipart/related; type="application/dicom"; ' f"boundary={boundary}"
            )
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": content_type_value,
                "Accept": "application/dicom+json",
            }

        try:
            response = requests.post(stow_url, data=body, headers=headers, timeout=300)
            response.raise_for_status()

            # Log Azure's response for debugging
            content_type_header = response.headers.get("Content-Type")
            logger.info(
                f"Azure response status: {response.status_code}, "
                f"Content-Type: {content_type_header}"
            )
            logger.info(f"Azure response length: {len(response.content)} bytes")

            # Return Azure's response (use .content for binary-safe handling)
            output.AnswerBuffer(
                response.content,
                response.headers.get("Content-Type", "application/json"),
            )
            logger.info(f"Successfully sent {len(resources)} instances to Azure DICOM")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send to Azure DICOM: {e}")
            error_details = {
                "error": "Failed to send to Azure DICOM",
                "details": str(e),
                "status_code": getattr(e.response, "status_code", None)
                if hasattr(e, "response")
                else None,
                "response_text": e.response.text
                if hasattr(e, "response") and e.response
                else None,
            }
            output.AnswerBuffer(json.dumps(error_details), "application/json")

    except Exception as e:
        logger.error(f"STOW-RS proxy failed: {type(e).__name__}: {e}", exc_info=True)
        error_response = {"error": str(e), "type": type(e).__name__}
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
    @app.before_request
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
    @app.route("/dicomweb-oauth/status", methods=["GET"])
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

    @app.route("/dicomweb-oauth/servers/<name>/test", methods=["POST"])
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
) -> int:
    """
    Orthanc incoming HTTP request callback - intercept STOW requests.

    Returns:
        0 to allow the request to proceed
        1 to deny the request
    """
    # Check if this is a STOW request to a configured server
    import re

    if method == "POST" and re.match(r"/dicom-web/servers/.+/stow", uri):
        print(f"DEBUG: Intercepted STOW request to {uri}", flush=True)
        # For now, just log it and allow it to proceed
        # TODO: Actually handle the request with OAuth
    return 0  # Allow request to proceed


# Plugin registration - only run when orthanc module is available
if _ORTHANC_AVAILABLE and orthanc is not None:
    try:
        print("DEBUG: Starting plugin registration", flush=True)
        logger.info("Registering DICOMweb OAuth plugin with Orthanc")
        initialize_plugin()
        print("DEBUG: Plugin initialized successfully", flush=True)

        # Register REST API endpoints
        print("DEBUG: About to register REST API endpoints", flush=True)
        logger.info("Registering REST API endpoints")
        orthanc.RegisterRestCallback("/dicomweb-oauth/status", handle_rest_api_status)
        orthanc.RegisterRestCallback("/dicomweb-oauth/servers", handle_rest_api_servers)
        orthanc.RegisterRestCallback(
            "/dicomweb-oauth/servers/(.*)/test", handle_rest_api_test_server
        )
        print("DEBUG: Registered standard endpoints", flush=True)

        # OVERRIDE DICOMweb plugin's STOW endpoint to inject OAuth transparently
        # This intercepts /dicom-web/servers/{name}/stow and adds OAuth automatically
        # Test endpoint to verify registration works
        def test_handler(output: Any, uri: str, **request: Any) -> None:
            print(f"DEBUG: TEST HANDLER CALLED! URI: {uri}", flush=True)
            output.AnswerBuffer(
                json.dumps({"test": "success", "uri": uri}), "application/json"
            )

        orthanc.RegisterRestCallback("/test-oauth-override", test_handler)
        print("DEBUG: Test endpoint registered at /test-oauth-override", flush=True)

        print("DEBUG: About to register OAuth STOW endpoint", flush=True)

        # Register OAuth proxy endpoints
        # DICOMweb plugin appends /studies to the base URL for STOW-RS requests
        # So we register at /oauth-dicom-web/servers/{server}/studies
        # Also register /stow for backward compatibility

        orthanc.RegisterRestCallback(
            "/oauth-dicom-web/servers/(.*)/studies", handle_rest_api_stow
        )
        print(
            "DEBUG: Registered OAuth STOW at /oauth-dicom-web/servers/(.*)/studies",
            flush=True,
        )
        logger.info(
            "Registered OAuth STOW-RS endpoint at /oauth-dicom-web/servers/(.*)/studies"
        )

        # Also register /stow for backward compatibility
        orthanc.RegisterRestCallback(
            "/oauth-dicom-web/servers/(.*)/stow", handle_rest_api_stow
        )
        print(
            "DEBUG: Registered fallback at /oauth-dicom-web/servers/(.*)/stow",
            flush=True,
        )
        logger.info(
            "Registered fallback OAuth endpoint at /oauth-dicom-web/servers/(.*)/stow"
        )

        orthanc.RegisterRestCallback("/dicomweb-oauth/metrics", metrics_endpoint)

        # Note: ExtendOrthancExplorer doesn't work with Orthanc Explorer 2
        # Instead, configure the DICOMweb server URL in orthanc.json to point
        # to http://localhost:8042/oauth-dicom-web/servers/azure-dicom
        # This makes the standard UI "Send to DICOMWeb server" button use
        # OAuth transparently
        logger.info(
            "DICOMweb OAuth plugin registered successfully. "
            "Configure DICOMweb server URL to "
            "http://localhost:8042/oauth-dicom-web/servers/{server-name} "
            "to enable transparent OAuth in Orthanc Explorer 2 UI"
        )
    except Exception as e:
        logger.error(f"Failed to register plugin: {e}")
        raise
