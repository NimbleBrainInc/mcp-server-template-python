"""Async HTTP client for Example API.

Replace this with your actual API client implementation.
"""

import os
from typing import Any

import aiohttp
from aiohttp import ClientError


class ExampleAPIError(Exception):
    """Exception raised for Example API errors."""

    def __init__(self, status: int, message: str, details: dict[str, Any] | None = None) -> None:
        self.status = status
        self.message = message
        self.details = details
        super().__init__(f"Example API Error {status}: {message}")


class ExampleClient:
    """Async client for Example API."""

    BASE_URL = "https://api.example.com/v1"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("EXAMPLE_API_KEY")
        if not self.api_key:
            raise ValueError("EXAMPLE_API_KEY is required")
        self.timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "ExampleClient":
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def _ensure_session(self) -> None:
        if not self._session:
            headers = {
                "User-Agent": "mcp-server-example/0.1.0",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            self._session = aiohttp.ClientSession(
                headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout)
            )

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: Any | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to the Example API."""
        await self._ensure_session()
        url = f"{self.BASE_URL}{path}"

        if params:
            params = {k: v for k, v in params.items() if v is not None}

        try:
            if not self._session:
                raise RuntimeError("Session not initialized")

            kwargs: dict[str, Any] = {}
            if json_data is not None:
                kwargs["json"] = json_data
            if params:
                kwargs["params"] = params

            async with self._session.request(method, url, **kwargs) as response:
                result = await response.json()

                if response.status >= 400:
                    error_msg = "Unknown error"
                    if isinstance(result, dict):
                        if "error" in result:
                            error_obj = result["error"]
                            if isinstance(error_obj, dict):
                                error_msg = error_obj.get("message", str(error_obj))
                            else:
                                error_msg = str(error_obj)
                        elif "message" in result:
                            error_msg = result["message"]

                    raise ExampleAPIError(response.status, error_msg, result)

                return result

        except ClientError as e:
            raise ExampleAPIError(500, f"Network error: {str(e)}") from e

    # ========================================================================
    # API Methods - Replace with your actual API methods
    # ========================================================================

    async def list_items(self, limit: int = 20) -> list[dict[str, Any]]:
        """List items from the API."""
        data = await self._request("GET", "/items", params={"limit": limit})
        return data.get("items", [])

    async def get_item(self, item_id: str) -> dict[str, Any]:
        """Get a single item by ID."""
        return await self._request("GET", f"/items/{item_id}")
