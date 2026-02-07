"""HTTP client abstraction for testability."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass
class HttpResponse:
    """HTTP response container."""

    status_code: int
    json_data: Optional[Dict[str, Any]] = None
    text: str = ""
    headers: Optional[Dict[str, str]] = None

    def __post_init__(self) -> None:
        if self.headers is None:
            self.headers = {}


class HttpClient(ABC):
    """
    Abstract HTTP client interface.

    Allows dependency injection and testing without actual HTTP calls.
    """

    @abstractmethod
    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        verify: bool = True,
        timeout: int = 30,
    ) -> HttpResponse:
        """
        Make HTTP POST request.

        Args:
            url: Target URL
            data: Form data (for x-www-form-urlencoded)
            json: JSON payload
            headers: HTTP headers
            verify: Verify SSL certificates
            timeout: Request timeout in seconds

        Returns:
            HttpResponse object

        Raises:
            requests.Timeout: If request times out
            requests.ConnectionError: If connection fails
            requests.RequestException: For other HTTP errors
        """
        pass

    @abstractmethod
    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        verify: bool = True,
        timeout: int = 30,
    ) -> HttpResponse:
        """
        Make HTTP GET request.

        Args:
            url: Target URL
            headers: HTTP headers
            verify: Verify SSL certificates
            timeout: Request timeout in seconds

        Returns:
            HttpResponse object

        Raises:
            requests.Timeout: If request times out
            requests.ConnectionError: If connection fails
            requests.RequestException: For other HTTP errors
        """
        pass


class RequestsHttpClient(HttpClient):
    """Default HTTP client using requests library."""

    def __init__(self, session: Optional[requests.Session] = None):
        """
        Initialize HTTP client.

        Args:
            session: Optional requests Session for connection pooling
        """
        self.session = session or requests.Session()

    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        verify: bool = True,
        timeout: int = 30,
    ) -> HttpResponse:
        """Make HTTP POST request."""
        response = self.session.post(
            url=url,
            data=data,
            json=json,
            headers=headers,
            verify=verify,
            timeout=timeout,
        )
        response.raise_for_status()

        return HttpResponse(
            status_code=response.status_code,
            json_data=response.json() if response.content else None,
            text=response.text,
            headers=dict(response.headers),
        )

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        verify: bool = True,
        timeout: int = 30,
    ) -> HttpResponse:
        """Make HTTP GET request."""
        response = self.session.get(
            url=url, headers=headers, verify=verify, timeout=timeout
        )
        response.raise_for_status()

        return HttpResponse(
            status_code=response.status_code,
            json_data=response.json() if response.content else None,
            text=response.text,
            headers=dict(response.headers),
        )
