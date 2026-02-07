"""Plugin context for dependency injection."""
from typing import Any, Dict, Optional

from src.token_manager import TokenManager


class PluginContext:
    """
    Central context for plugin state and dependencies.

    Replaces global variables with dependency injection pattern.
    All plugin state is encapsulated in this class.
    """

    def __init__(self) -> None:
        self.token_managers: Dict[str, TokenManager] = {}
        self.server_urls: Dict[str, str] = {}
        self.audit_logger: Optional[Any] = None  # Will add later
        self.metrics_collector: Optional[Any] = None  # Will add later

    def get_token_manager(self, server_name: str) -> Optional[TokenManager]:
        """Get token manager for a server."""
        return self.token_managers.get(server_name)

    def get_server_url(self, server_name: str) -> Optional[str]:
        """Get URL for a server."""
        return self.server_urls.get(server_name)

    def find_server_for_uri(self, uri: str) -> Optional[str]:
        """Find which configured server a URI belongs to."""
        for server_name, server_url in self.server_urls.items():
            if uri.startswith(server_url):
                return server_name
        return None

    def register_token_manager(self, server_name: str, manager: TokenManager, url: str):
        """Register a token manager for a server."""
        self.token_managers[server_name] = manager
        self.server_urls[server_name] = url
