"""
Smoke test: verify the LLM reads the skill resource and selects the correct tool.

Requires ANTHROPIC_API_KEY and EXAMPLE_API_KEY in environment.
"""

import os

import anthropic
import pytest
from fastmcp import Client

from mcp_example.server import mcp


def get_anthropic_client() -> anthropic.Anthropic:
    token = os.environ.get("ANTHROPIC_API_KEY")
    if not token:
        pytest.skip("ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=token)


async def get_server_context() -> dict:
    """Extract instructions, skill content, and tool definitions from the MCP server."""
    async with Client(mcp) as client:
        init = await client.initialize()
        instructions = init.instructions

        resources = await client.list_resources()
        skill_text = ""
        for r in resources:
            if "skill://" in str(r.uri):
                contents = await client.read_resource(str(r.uri))
                skill_text = contents[0].text if hasattr(contents[0], "text") else str(contents[0])

        tools_list = await client.list_tools()
        tools = []
        for t in tools_list:
            tool_def = {
                "name": t.name,
                "description": t.description or "",
                "input_schema": t.inputSchema,
            }
            tools.append(tool_def)

        return {
            "instructions": instructions,
            "skill": skill_text,
            "tools": tools,
        }


class TestSkillLLMInvocation:
    """Test that an LLM reads the skill and makes correct tool choices.

    TODO: Replace with tests specific to your server's tools and skill.

    Each test should:
    1. Send a user prompt that maps to a specific tool per the SKILL.md
    2. Assert the LLM calls the expected tool (not a similar one)
    """

    # @pytest.mark.asyncio
    # async def test_query_selects_correct_tool(self):
    #     """When asked to X, the LLM should call tool_name."""
    #     ctx = await get_server_context()
    #     client = get_anthropic_client()
    #
    #     system = (
    #         f"You are an assistant.\n\n"
    #         f"## Server Instructions\n{ctx['instructions']}\n\n"
    #         f"## Skill Resource\n{ctx['skill']}"
    #     )
    #
    #     response = client.messages.create(
    #         model="claude-haiku-4-5-20251001",
    #         max_tokens=1024,
    #         system=system,
    #         messages=[{"role": "user", "content": "Your test prompt here"}],
    #         tools=[{"type": "custom", **t} for t in ctx["tools"]],
    #     )
    #
    #     tool_calls = [b for b in response.content if b.type == "tool_use"]
    #     assert len(tool_calls) > 0, "LLM did not call any tool"
    #     assert tool_calls[0].name == "expected_tool_name"
    pass
