"""
Orthanc DICOMweb OAuth2 Plugin.

Generic OAuth2/OIDC token management plugin for Orthanc's DICOMweb connections.
Automatically acquires, caches, and refreshes bearer tokens for any OAuth2-protected
DICOMweb endpoint.
"""
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

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
    Flask = None  # type: ignore[assignment]
    jsonify = None  # type: ignore[assignment]
    request = None  # type: ignore[assignment]

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
            logger.info("Configuring OAuth for server: %s", server_name)

            manager = TokenManager(server_name, server_config)
            context.register_token_manager(
                server_name=server_name, manager=manager, url=server_config["Url"]
            )

            logger.info(
                "Server '%s' configured with URL: %s",
                server_name,
                server_config["Url"],
            )

        logger.info("DICOMweb OAuth plugin initialized with %d server(s)", len(servers))

    except ConfigError as config_err:
        logger.error("Configuration error: %s", config_err)
        raise
    except Exception as init_err:
        logger.error("Failed to initialize plugin: %s", init_err)
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
    return {
        "plugin_version": PLUGIN_VERSION,
        "api_version": API_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "data": data,
    }


def handle_rest_api_status(output: Any, _uri: str, **_request: Any) -> None:
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

    except Exception as status_err:
        logger.error(
            "Status endpoint failed: %s: %s", type(status_err).__name__, status_err
        )
        error_response = create_api_response(
            {"status": "error", "error": str(status_err)}
        )
        output.AnswerBuffer(json.dumps(error_response), "application/json")


def handle_rest_api_servers(output: Any, _uri: str, **_request: Any) -> None:
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

    except Exception as servers_err:
        logger.error(
            "Servers endpoint failed: %s: %s",
            type(servers_err).__name__,
            servers_err,
        )
        error_response = create_api_response({"error": str(servers_err)})
        output.AnswerBuffer(json.dumps(error_response), "application/json")


def _extract_server_name(uri: str) -> tuple[str | None, str | None]:
    """Extract server name from URI path.

    Args:
        uri: Request URI path

    Returns:
        Tuple of (server_name, error_message). If successful, error is None.
    """
    parts = uri.split("/")
    if len(parts) < 5:
        return None, "Server name not specified"
    return parts[3], None


def _build_multipart_from_resources(
    resources: list[str], boundary: str, orthanc_module: Any
) -> tuple[bytes | None, str | None]:
    """Build multipart DICOM message from resource IDs.

    Args:
        resources: List of Orthanc resource IDs
        boundary: MIME boundary string
        orthanc_module: Orthanc module

    Returns:
        Tuple of (multipart_body, error_message). If successful, error is None.
    """
    multipart_data = []
    for resource_id in resources:
        try:
            dicom_data = orthanc_module.RestApiGet(f"/instances/{resource_id}/file")
            part_header = f"--{boundary}\r\n"
            part_header += "Content-Type: application/dicom\r\n\r\n"
            multipart_data.append(part_header.encode("utf-8"))
            multipart_data.append(dicom_data)
            multipart_data.append(b"\r\n")
        except Exception as dicom_err:
            logger.error("Failed to get DICOM file for %s: %s", resource_id, dicom_err)
            return None, f"Failed to get DICOM file: {str(dicom_err)}"

    multipart_data.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(multipart_data), None


def _get_stow_url(context: Any, server_name: str, output: Any) -> str | None:
    """Get STOW-RS URL for server.

    Args:
        context: Plugin context
        server_name: Name of the configured server
        output: Orthanc output for error responses

    Returns:
        STOW-RS URL, or None if not found (error already sent to output).
    """
    server_url = context.get_server_url(server_name)
    if not server_url:
        output.AnswerBuffer(
            json.dumps({"error": f"Server URL not found for '{server_name}'"}),
            "application/json",
        )
        return None
    return f"{server_url.rstrip('/')}/studies"


def _get_oauth_token(context: Any, server_name: str, output: Any) -> str | None:
    """Get OAuth token for server.

    Args:
        context: Plugin context
        server_name: Name of the configured server
        output: Orthanc output for error responses

    Returns:
        OAuth token string, or None if failed (error sent to output).
    """
    token_manager = context.get_token_manager(server_name)
    if not token_manager:
        output.AnswerBuffer(
            json.dumps({"error": f"Server '{server_name}' not configured"}),
            "application/json",
        )
        return None

    try:
        token = token_manager.get_token()
        return str(token) if token else None
    except TokenAcquisitionError as token_err:
        logger.error("Failed to acquire token for '%s': %s", server_name, token_err)
        error_data = {
            "error": "OAuth token acquisition failed",
            "details": str(token_err),
        }
        output.AnswerBuffer(json.dumps(error_data), "application/json")
        return None


def _prepare_request_body_and_headers(
    content_type: str, body: bytes, orthanc_module: Any
) -> tuple[bytes | None, dict[str, str] | None, str | None]:
    """Prepare request body and headers based on content type.

    Args:
        content_type: Request content type
        body: Request body as bytes
        orthanc_module: Orthanc module

    Returns:
        Tuple of (body, headers_dict, error_message). If successful, error is None.
    """
    if "multipart/related" in content_type:
        # DICOMweb plugin is sending pre-formatted multipart DICOM data
        logger.info("Forwarding multipart DICOM data (%d bytes)", len(body))
        extra_headers = {
            "Content-Type": content_type,
            "Accept": "application/dicom+json",
        }
        return body, extra_headers, None

    # JSON request with resource IDs - build multipart ourselves
    return _prepare_json_request(body, orthanc_module)


def _prepare_json_request(
    body: bytes, orthanc_module: Any
) -> tuple[bytes | None, dict[str, str] | None, str | None]:
    """Prepare DICOM data from JSON request with resource IDs.

    Args:
        body: Request body as bytes
        orthanc_module: Orthanc module

    Returns:
        Tuple of (body, headers_dict, error_message). If successful, error is None.
    """
    try:
        body_str = body.decode("utf-8") if isinstance(body, bytes) else body
        request_data = json.loads(body_str) if body_str else {}
        resources = request_data.get("Resources", [])
    except (UnicodeDecodeError, json.JSONDecodeError) as decode_err:
        return None, None, f"Invalid request body: {type(decode_err).__name__}"

    if not resources:
        return None, None, "No resources specified"

    logger.info("Building multipart from %d resources", len(resources))

    boundary = uuid.uuid4().hex
    multipart_body, error = _build_multipart_from_resources(
        resources, boundary, orthanc_module
    )
    if error:
        return None, None, error

    content_type = f'multipart/related; type="application/dicom"; boundary={boundary}'
    headers_dict = {"Content-Type": content_type, "Accept": "application/dicom+json"}
    return multipart_body, headers_dict, None


def _send_dicom_to_server(
    stow_url: str, body: bytes, headers: dict[str, str], output: Any
) -> None:
    """Send DICOM data to remote server and handle response.

    Args:
        stow_url: STOW-RS endpoint URL
        body: DICOM data as bytes
        headers: HTTP headers including OAuth token
        output: Orthanc output object for response
    """
    try:
        response = requests.post(stow_url, data=body, headers=headers, timeout=300)
        response.raise_for_status()

        # Log Azure's response for debugging
        content_type_header = response.headers.get("Content-Type")
        logger.info(
            "Azure response status: %d, Content-Type: %s",
            response.status_code,
            content_type_header,
        )
        logger.info("Azure response length: %d bytes", len(response.content))

        # Return Azure's response (use .content for binary-safe handling)
        output.AnswerBuffer(
            response.content,
            response.headers.get("Content-Type", "application/json"),
        )
        logger.info("Successfully sent DICOM data to remote server")

    except requests.exceptions.RequestException as req_err:
        logger.error("Failed to send to remote DICOM server: %s", req_err)
        error_details = {
            "error": "Failed to send to remote DICOM server",
            "details": str(req_err),
            "status_code": getattr(req_err.response, "status_code", None)
            if hasattr(req_err, "response")
            else None,
            "response_text": req_err.response.text
            if hasattr(req_err, "response") and req_err.response
            else None,
        }
        output.AnswerBuffer(json.dumps(error_details), "application/json")


def _process_stow_request(
    output: Any, uri: str, req_data: Any, orthanc_module: Any
) -> None:
    """Process STOW-RS request with OAuth.

    Args:
        output: Orthanc output object
        uri: Request URI
        req_data: Request data
        orthanc_module: Orthanc module
    """
    context = get_plugin_context()

    # Extract server name from URI
    server_name, error = _extract_server_name(uri)
    if error or server_name is None:
        output.AnswerBuffer(
            json.dumps({"error": error or "Invalid server name"}),
            "application/json",
        )
        return

    # Get OAuth token and server URL
    token = _get_oauth_token(context, server_name, output)
    if not token:
        return  # Error already sent to output

    stow_url = _get_stow_url(context, server_name, output)
    if not stow_url:
        return  # Error already sent to output

    # Prepare request body and headers based on content type
    content_type = req_data.get("headers", {}).get("content-type", "")
    request_body = req_data.get("body", b"")

    body, extra_headers, error = _prepare_request_body_and_headers(
        content_type, request_body, orthanc_module
    )
    if error or body is None or extra_headers is None:
        output.AnswerBuffer(
            json.dumps({"error": error or "Failed to prepare request"}),
            "application/json",
        )
        return

    # Add OAuth token to headers
    headers = {"Authorization": f"Bearer {token}", **extra_headers}

    # Send DICOM data to remote server
    _send_dicom_to_server(stow_url, body, headers, output)


def handle_rest_api_stow(output: Any, uri: str, **req_data: Any) -> None:
    """Proxy STOW-RS requests with automatic OAuth token injection.

    POST /dicomweb-oauth/servers/{name}/stow

    Acts as a transparent proxy between DICOMweb plugin and remote DICOM server.

    Request body: Same as Orthanc's native STOW-RS endpoint
    {
        "Resources": ["orthanc-id-1", "orthanc-id-2"],
        "Synchronous": true/false,
        "Priority": 0
    }
    """
    print(f"DEBUG: handle_rest_api_stow CALLED! URI: {uri}", flush=True)
    # Import orthanc locally to avoid import errors during testing
    import orthanc  # pylint: disable=import-error

    try:
        print("DEBUG: Got plugin context", flush=True)
        print(f"DEBUG: Request headers: {req_data.get('headers', {})}", flush=True)
        body_len = len(req_data.get("body", b"")) if req_data.get("body") else 0
        print(f"DEBUG: Request body length: {body_len}", flush=True)

        # Process the STOW request with OAuth
        _process_stow_request(output, uri, req_data, orthanc)

    except Exception as stow_err:
        logger.error(
            "STOW-RS proxy failed: %s: %s",
            type(stow_err).__name__,
            stow_err,
            exc_info=True,
        )
        error_response = {"error": str(stow_err), "type": type(stow_err).__name__}
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

    except TokenAcquisitionError as test_err:
        result = {"server": server_name, "status": "error", "error": str(test_err)}
        output.AnswerBuffer(
            json.dumps(result, indent=2), "application/json", status=503
        )


def metrics_endpoint(output: Any, _uri: str, **_request: Any) -> None:
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
    except Exception as metrics_err:
        logger.error("Failed to generate metrics: %s", metrics_err)
        error_message = f"Error generating metrics: {metrics_err}"
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
    app.rate_limiter = RateLimiter(  # type: ignore[attr-defined]
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
            app.rate_limiter.check_rate_limit(client_key)  # type: ignore[attr-defined]
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
        except Exception as flask_err:
            error_response = create_api_response(
                {"status": "error", "error": str(flask_err)}
            )
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

        except TokenAcquisitionError as flask_token_err:
            result = {"server": name, "status": "error", "error": str(flask_token_err)}
            return jsonify(result), 503

    return app


# Orthanc plugin entry point
def OnChange(_changeType: int, _level: int, _resource: str) -> None:
    """Orthanc change callback (not used, but required by plugin API)."""


def OnIncomingHttpRequest(
    method: str, uri: str, _ip: str, _username: str, _headers: Dict[str, str]
) -> int:
    """
    Orthanc incoming HTTP request callback - intercept STOW requests.

    Returns:
        0 to allow the request to proceed
        1 to deny the request
    """
    # Check if this is a STOW request to a configured server
    if method == "POST" and re.match(r"/dicom-web/servers/.+/stow", uri):
        print(f"DEBUG: Intercepted STOW request to {uri}", flush=True)
        # For now, just log it and allow it to proceed
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
        def test_handler(output: Any, uri: str, **_request: Any) -> None:
            """Test handler to verify REST endpoint registration."""
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
    except Exception as register_err:
        logger.error("Failed to register plugin: %s", register_err)
        raise
