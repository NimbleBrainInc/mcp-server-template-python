"""Unit tests for the Example API client."""

import os
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from mcp_example.api_client import ExampleAPIError, ExampleClient


@pytest_asyncio.fixture
async def mock_client():
    """Create an ExampleClient with mocked session."""
    client = ExampleClient(api_key="test_key")
    client._session = AsyncMock()
    yield client
    await client.close()


class TestClientInitialization:
    """Test client creation and configuration."""

    def test_init_with_explicit_key(self):
        """Client accepts an explicit API key."""
        client = ExampleClient(api_key="explicit_key")
        assert client.api_key == "explicit_key"

    def test_init_with_env_var(self):
        """Client falls back to EXAMPLE_API_KEY env var."""
        os.environ["EXAMPLE_API_KEY"] = "env_key"
        try:
            client = ExampleClient()
            assert client.api_key == "env_key"
        finally:
            del os.environ["EXAMPLE_API_KEY"]

    def test_init_without_key_raises(self):
        """Client raises ValueError when no key is available."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("EXAMPLE_API_KEY", None)
            with pytest.raises(ValueError, match="EXAMPLE_API_KEY is required"):
                ExampleClient()

    def test_custom_timeout(self):
        """Client accepts a custom timeout."""
        client = ExampleClient(api_key="key", timeout=60.0)
        assert client.timeout == 60.0

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Client works as an async context manager."""
        async with ExampleClient(api_key="test") as client:
            assert client._session is not None
        assert client._session is None


class TestClientMethods:
    """Test API client methods with mocked responses."""

    @pytest.mark.asyncio
    async def test_list_items(self, mock_client):
        """Test list items endpoint."""
        mock_response = {"items": [{"id": "1", "name": "Item 1"}, {"id": "2", "name": "Item 2"}]}
        with patch.object(mock_client, "_request", return_value=mock_response):
            result = await mock_client.list_items(limit=10)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_item(self, mock_client):
        """Test get item endpoint."""
        mock_response = {"id": "1", "name": "Item 1", "description": "Test"}
        with patch.object(mock_client, "_request", return_value=mock_response):
            result = await mock_client.get_item("1")
        assert result["id"] == "1"


class TestErrorHandling:
    """Test error handling for API errors."""

    @pytest.mark.asyncio
    async def test_401_unauthorized(self, mock_client):
        """Test handling of unauthorized errors."""
        with patch.object(
            mock_client,
            "_request",
            side_effect=ExampleAPIError(401, "Invalid API key"),
        ):
            with pytest.raises(ExampleAPIError) as exc_info:
                await mock_client.list_items()
            assert exc_info.value.status == 401

    @pytest.mark.asyncio
    async def test_429_rate_limit(self, mock_client):
        """Test handling of rate limit errors."""
        with patch.object(
            mock_client,
            "_request",
            side_effect=ExampleAPIError(429, "Rate limit exceeded"),
        ):
            with pytest.raises(ExampleAPIError) as exc_info:
                await mock_client.list_items()
            assert exc_info.value.status == 429

    @pytest.mark.asyncio
    async def test_network_error(self, mock_client):
        """Test handling of network errors."""
        with patch.object(
            mock_client,
            "_request",
            side_effect=ExampleAPIError(500, "Network error: Connection failed"),
        ):
            with pytest.raises(ExampleAPIError) as exc_info:
                await mock_client.list_items()
            assert exc_info.value.status == 500
            assert "Network error" in exc_info.value.message

    def test_error_string_representation(self):
        """Test error string format."""
        err = ExampleAPIError(401, "Unauthorized", {"id": "auth_error"})
        assert "401" in str(err)
        assert "Unauthorized" in str(err)
        assert err.details == {"id": "auth_error"}
