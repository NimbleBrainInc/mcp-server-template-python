"""Shared fixtures for unit tests."""

from unittest.mock import AsyncMock

import pytest

from mcp_example.server import mcp

# Longer than any listing row may carry, so a row that leaks it fails assert_bounded_rows.
LONG_DESCRIPTION = "A long description. " * 100


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
            {"id": "1", "name": "Item 1", "description": LONG_DESCRIPTION},
            {"id": "2", "name": "Item 2", "description": LONG_DESCRIPTION},
        ]
    )
    client.get_item = AsyncMock(
        return_value={
            "id": "1",
            "name": "Item 1",
            "description": LONG_DESCRIPTION,
        }
    )
    return client
