"""Tests for the Example MCP server: its skill, its tools and its errors.

A host may connect on either protocol era, so every test that crosses the wire runs on
both: `"auto"` negotiates 2026-07-28 and `"legacy"` runs the 2025-11-25 handshake.
"""

import json
from unittest.mock import patch

import pytest
from fastmcp import Client
from mcp.shared.exceptions import MCPError
from nimblebrain_server_sdk.testing import Mode, assert_bounded_rows, served_skills

from mcp_example.api_client import ExampleAPIError
from mcp_example.server import SKILLS_DIR
from tests.conftest import LONG_DESCRIPTION

MODES: list[Mode] = ["auto", "legacy"]  # 2026-07-28, then 2025-11-25
SKILL_URI = "skill://example/SKILL.md"


@pytest.mark.parametrize("mode", MODES)
class TestSkill:
    """The skill a host reads before it uses the tools."""

    async def test_skill_is_served(self, mcp_server, mode: Mode):
        """served_skills reads every skill file back and checks it against its listing."""
        skills = await served_skills(mcp_server, mode)
        assert set(skills) == {SKILL_URI}
        frontmatter = skills[SKILL_URI]["frontmatter"]
        assert frontmatter["name"] == "example"
        assert frontmatter["description"]

    async def test_instructions_name_the_skill(self, mcp_server, mode: Mode):
        """Server instructions point at a resource the server serves."""
        async with Client(mcp_server, mode=mode) as client:
            assert client.instructions is not None
            assert SKILL_URI in client.instructions
            (content,) = await client.read_resource(SKILL_URI)
        assert content.text == (SKILLS_DIR / "example" / "SKILL.md").read_text()

    async def test_skill_names_every_tool(self, mcp_server, mode: Mode):
        """The skill covers each tool the server lists."""
        async with Client(mcp_server, mode=mode) as client:
            tools = await client.list_tools()
        skill = (SKILLS_DIR / "example" / "SKILL.md").read_text()
        for tool in tools:
            assert f"`{tool.name}`" in skill


@pytest.mark.parametrize("mode", MODES)
class TestToolListing:
    """What a host learns about the tools before it calls one."""

    async def test_all_tools_listed(self, mcp_server, mode: Mode):
        """All expected tools appear in tool listing."""
        async with Client(mcp_server, mode=mode) as client:
            tools = await client.list_tools()
        assert {t.name for t in tools} == {"list_items", "get_item"}

    async def test_every_tool_is_annotated(self, mcp_server, mode: Mode):
        """A tool with no annotation reads to a client as a destructive write."""
        async with Client(mcp_server, mode=mode) as client:
            tools = await client.list_tools()
        for tool in tools:
            assert tool.annotations is not None, tool.name
            assert tool.annotations.read_only_hint is not None, tool.name


@pytest.mark.parametrize("mode", MODES)
class TestTools:
    """The tools, called the way a host calls them."""

    async def test_list_items_returns_bounded_rows(self, mcp_server, mock_client, mode: Mode):
        """A listing row carries its address and a preview, never the whole description."""
        with patch("mcp_example.server.get_client", return_value=mock_client):
            async with Client(mcp_server, mode=mode) as client:
                result = await client.call_tool("list_items", {"limit": 10})
        mock_client.list_items.assert_called_once_with(limit=10)
        rows = result.data
        assert_bounded_rows(rows, unbounded=["description"])
        assert [row["uri"] for row in rows] == ["example://items/1", "example://items/2"]
        assert LONG_DESCRIPTION.startswith(rows[0]["description_preview"].rstrip("…"))

    async def test_get_item_returns_the_whole_item(self, mcp_server, mock_client, mode: Mode):
        """get_item returns the fields a listing row cuts short."""
        with patch("mcp_example.server.get_client", return_value=mock_client):
            async with Client(mcp_server, mode=mode) as client:
                result = await client.call_tool("get_item", {"item_id": "1"})
        mock_client.get_item.assert_called_once_with("1")
        assert result.data == {"id": "1", "name": "Item 1", "description": LONG_DESCRIPTION}


@pytest.mark.parametrize("mode", MODES)
class TestItemResource:
    """The address a listing row carries reads back the whole record."""

    async def test_a_row_uri_reads_the_whole_item(self, mcp_server, mock_client, mode: Mode):
        """Reading the uri from a list_items row returns what get_item returns."""
        with patch("mcp_example.server.get_client", return_value=mock_client):
            async with Client(mcp_server, mode=mode) as client:
                rows = (await client.call_tool("list_items", {})).data
                (content,) = await client.read_resource(rows[0]["uri"])
                item = (await client.call_tool("get_item", {"item_id": rows[0]["id"]})).data
        assert content.mime_type == "application/json"
        assert json.loads(content.text) == item
        assert item["description"] == LONG_DESCRIPTION

    async def test_the_item_address_is_listed(self, mcp_server, mode: Mode):
        """A host finds the address shape in the resource templates."""
        async with Client(mcp_server, mode=mode) as client:
            templates = await client.list_resource_templates()
        assert [t.uri_template for t in templates] == ["example://items/{item_id}"]

    async def test_a_missing_item_fails_the_read(self, mcp_server, mock_client, mode: Mode):
        """A failed read carries the classified message, not the API's own text."""
        mock_client.get_item.side_effect = ExampleAPIError(404, "no row in items_v2")
        with patch("mcp_example.server.get_client", return_value=mock_client):
            async with Client(mcp_server, mode=mode) as client:
                with pytest.raises(MCPError) as failure:
                    await client.read_resource("example://items/missing")
        assert "The requested resource was not found." in str(failure.value)
        assert "items_v2" not in str(failure.value)


async def call_for_error(mcp_server, mode: Mode, tool, arguments):
    """Call a tool that must fail, and return the error a host receives."""
    async with Client(mcp_server, mode=mode) as client:
        result = await client.call_tool(tool, arguments, raise_on_error=False)
    assert result.is_error
    return result.structured_content["error"]


@pytest.mark.parametrize("mode", MODES)
class TestErrors:
    """A failure reaches the caller as an error with a code it can act on."""

    @pytest.mark.parametrize(
        ("tool", "arguments", "message"),
        [
            ("list_items", {"limit": 0}, "`limit` must be between 1 and 100."),
            ("list_items", {"limit": 101}, "`limit` must be between 1 and 100."),
            ("get_item", {"item_id": " "}, "`item_id` is empty."),
        ],
    )
    async def test_a_caller_mistake_is_bad_input(
        self, mcp_server, mode: Mode, tool, arguments, message
    ):
        """A bad argument is refused before the API is called."""
        with patch("mcp_example.server.get_client") as get_client:
            error = await call_for_error(mcp_server, mode, tool, arguments)
        get_client.assert_not_called()
        assert error == {"code": "bad_input", "retryable": False, "message": message}

    async def test_a_missing_item_is_not_found(self, mcp_server, mock_client, mode: Mode):
        """An API 404 is classified, and the API's own text stays out of the result."""
        mock_client.get_item.side_effect = ExampleAPIError(404, "no row in items_v2")
        with patch("mcp_example.server.get_client", return_value=mock_client):
            error = await call_for_error(mcp_server, mode, "get_item", {"item_id": "missing"})
        assert error == {
            "code": "not_found",
            "retryable": False,
            "message": "The requested resource was not found.",
            "upstream_status": 404,
        }

    async def test_a_rate_limit_is_retryable(self, mcp_server, mock_client, mode: Mode):
        """An API 429 tells the caller a retry can help."""
        mock_client.list_items.side_effect = ExampleAPIError(429, "Rate limit exceeded")
        with patch("mcp_example.server.get_client", return_value=mock_client):
            error = await call_for_error(mcp_server, mode, "list_items", {})
        assert error["code"] == "rate_limited"
        assert error["retryable"] is True
        assert error["upstream_status"] == 429

    async def test_a_missing_api_key_is_auth_required(self, mcp_server, monkeypatch, mode: Mode):
        """Without EXAMPLE_API_KEY the caller sees why the tool failed."""
        monkeypatch.delenv("EXAMPLE_API_KEY", raising=False)
        monkeypatch.setattr("mcp_example.server._client", None)
        error = await call_for_error(mcp_server, mode, "list_items", {})
        assert error == {
            "code": "auth_required",
            "retryable": False,
            "message": "EXAMPLE_API_KEY environment variable is required",
        }
