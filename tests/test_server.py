"""Tests for Example MCP Server tools and skill resource."""

from unittest.mock import patch

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from mcp_example.api_client import ExampleAPIError
from mcp_example.server import SKILL_CONTENT


class TestSkillResource:
    """Test the skill resource and server instructions."""

    @pytest.mark.asyncio
    async def test_initialize_returns_instructions(self, mcp_server):
        """Server instructions reference the skill resource."""
        async with Client(mcp_server) as client:
            result = await client.initialize()
            assert result.instructions is not None
            assert "skill://example/usage" in result.instructions

    @pytest.mark.asyncio
    async def test_skill_resource_listed(self, mcp_server):
        """skill://example/usage appears in resource listing."""
        async with Client(mcp_server) as client:
            resources = await client.list_resources()
            uris = [str(r.uri) for r in resources]
            assert "skill://example/usage" in uris

    @pytest.mark.asyncio
    async def test_skill_resource_readable(self, mcp_server):
        """Reading the skill resource returns the full skill content."""
        async with Client(mcp_server) as client:
            contents = await client.read_resource("skill://example/usage")
            text = contents[0].text if hasattr(contents[0], "text") else str(contents[0])
            assert "list_items" in text
            assert "get_item" in text

    @pytest.mark.asyncio
    async def test_skill_content_matches_constant(self, mcp_server):
        """Resource content matches the SKILL_CONTENT constant."""
        async with Client(mcp_server) as client:
            contents = await client.read_resource("skill://example/usage")
            text = contents[0].text if hasattr(contents[0], "text") else str(contents[0])
            assert text == SKILL_CONTENT


class TestToolListing:
    """Test that all tools are registered and discoverable."""

    @pytest.mark.asyncio
    async def test_all_tools_listed(self, mcp_server):
        """All expected tools appear in tool listing."""
        async with Client(mcp_server) as client:
            tools = await client.list_tools()
            names = {t.name for t in tools}
            expected = {"list_items", "get_item"}
            assert expected == names


class TestMCPTools:
    """Test the MCP server tools via FastMCP Client."""

    @pytest.mark.asyncio
    async def test_list_items(self, mcp_server, mock_client):
        """Test list_items tool."""
        with patch("mcp_example.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool("list_items", {"limit": 10})
            assert result is not None
            mock_client.list_items.assert_called_once_with(limit=10)

    @pytest.mark.asyncio
    async def test_get_item(self, mcp_server, mock_client):
        """Test get_item tool."""
        with patch("mcp_example.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool("get_item", {"item_id": "1"})
            assert result is not None
            mock_client.get_item.assert_called_once_with("1")

    @pytest.mark.asyncio
    async def test_list_items_api_error(self, mcp_server, mock_client):
        """Test list_items handles API errors."""
        mock_client.list_items.side_effect = ExampleAPIError(401, "Unauthorized")
        with patch("mcp_example.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                with pytest.raises(ToolError, match="401"):
                    await client.call_tool("list_items", {})
