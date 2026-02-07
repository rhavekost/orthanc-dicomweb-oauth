"""Plugin context management using singleton pattern."""
import logging
import threading
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PluginContext:
    """
    Singleton plugin context for managing token managers.

    Replaces global state pattern with thread-safe singleton.
    """

    _instance: Optional["PluginContext"] = None
    _initialized: bool = False
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "PluginContext":
        """Prevent direct instantiation."""
        raise RuntimeError(
            "PluginContext cannot be instantiated directly. "
            "Use get_instance() instead."
        )

    @classmethod
    def get_instance(cls) -> "PluginContext":
        """
        Get singleton instance of PluginContext (thread-safe).

        Returns:
            Singleton PluginContext instance
        """
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking pattern
                if cls._instance is None:
                    # Bypass __new__ for singleton creation
                    instance = object.__new__(cls)
                    instance._initialize()
                    cls._instance = instance
                    cls._initialized = True

        return cls._instance

    def _initialize(self) -> None:
        """Initialize singleton instance."""
        self._token_managers: Dict[str, Any] = {}
        self._server_urls: Dict[str, str] = {}
        self._logger = logging.getLogger(__name__)

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset singleton instance (for testing only).

        WARNING: This should only be used in tests.
        """
        with cls._lock:
            cls._instance = None
            cls._initialized = False

    def register_token_manager(self, server_name: str, manager: Any, url: str) -> None:
        """
        Register a token manager for a DICOMweb server.

        Args:
            server_name: Name of the server
            manager: TokenManager instance
            url: Server URL
        """
        self._token_managers[server_name] = manager
        self._server_urls[server_name] = url
        self._logger.info(f"Registered token manager for server: {server_name}")

    def get_token_manager(self, server_name: str) -> Optional[Any]:
        """
        Get token manager for a server.

        Args:
            server_name: Name of the server

        Returns:
            TokenManager instance or None if not found
        """
        return self._token_managers.get(server_name)

    def get_server_url(self, server_name: str) -> Optional[str]:
        """
        Get URL for a server.

        Args:
            server_name: Name of the server

        Returns:
            Server URL or None if not found
        """
        return self._server_urls.get(server_name)

    def find_server_for_url(self, url: str) -> Optional[str]:
        """
        Find server name for a given URL.

        Args:
            url: URL to match

        Returns:
            Server name or None if no match
        """
        for server_name, server_url in self._server_urls.items():
            if url.startswith(server_url):
                return server_name
        return None

    def get_all_servers(self) -> Dict[str, str]:
        """
        Get all registered servers.

        Returns:
            Dictionary mapping server names to URLs
        """
        return self._server_urls.copy()

    @property
    def token_managers(self) -> Dict[str, Any]:
        """Get all token managers (read-only access)."""
        return self._token_managers

    @property
    def server_urls(self) -> Dict[str, str]:
        """Get all server URLs (read-only access)."""
        return self._server_urls
