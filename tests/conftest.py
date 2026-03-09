"""Shared fixtures for unit tests."""

from unittest.mock import AsyncMock

import pytest

from mcp_example.server import mcp


@pytest.fixture
def mcp_server():
    """Return the MCP server instance."""
    return mcp


@pytest.fixture
def mock_client():
    """Create a mock API client."""
    client = AsyncMock()
    client.list_items = AsyncMock(
        return_value=[
            {"id": "1", "name": "Item 1"},
            {"id": "2", "name": "Item 2"},
        ]
    )
    client.get_item = AsyncMock(
        return_value={
            "id": "1",
            "name": "Item 1",
            "description": "Test item",
        }
    )
    return client
