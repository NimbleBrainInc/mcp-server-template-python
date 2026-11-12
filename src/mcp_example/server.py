"""Example MCP Server - FastMCP Implementation.

This is a template server. Replace 'example' with your service name and
implement the tools for your API.

Getting started:
1. Rename this package from mcp_example to mcp_<yourservice>
2. Update manifest.json, server.json, pyproject.toml with your service info
3. Implement your API client in api_client.py
4. Add Pydantic models in api_models.py
5. Add tools below using @mcp.tool()
"""

import logging
import os
import sys
from importlib.resources import files

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_example.api_client import ExampleAPIError, ExampleClient

# Logging setup - all logs to stderr (stdout is reserved for JSON-RPC). Diagnostics go
# here, never to the client: MCP's logging capability is deprecated as of the 2026-07-28
# protocol (SEP-2577). A failure the caller must see is raised as a ToolError.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_example")

logger.info("Example server module loading...")

SKILL_CONTENT = files("mcp_example").joinpath("SKILL.md").read_text()

# Create MCP server
mcp = FastMCP(
    "Example",
    instructions=(
        "Before using tools, read the skill://example/usage resource "
        "for tool selection guidance and workflow patterns."
    ),
)

# Global client instance (lazy initialization)
_client: ExampleClient | None = None


async def get_client() -> ExampleClient:
    """Get or create the API client instance.

    Raises:
        ToolError: when EXAMPLE_API_KEY is not set, so the caller sees why the tool failed.
    """
    global _client
    if _client is None:
        api_key = os.environ.get("EXAMPLE_API_KEY")
        if not api_key:
            logger.error("EXAMPLE_API_KEY is not set")
            raise ToolError("EXAMPLE_API_KEY environment variable is required")
        _client = ExampleClient(api_key=api_key)
    return _client


# Health endpoint for HTTP transport
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for monitoring."""
    return JSONResponse({"status": "healthy", "service": "mcp-example"})


# ============================================================================
# Tools - Add your MCP tools below
# ============================================================================


@mcp.tool()
async def list_items(
    limit: int = 20,
) -> list[dict]:
    """List items from the Example API.

    Args:
        limit: Maximum number of items to return (1-100, default 20)

    Returns:
        List of items
    """
    client = await get_client()
    try:
        return await client.list_items(limit=limit)
    except ExampleAPIError as e:
        logger.warning("list_items failed: %s", e)
        raise ToolError(str(e)) from e


@mcp.tool()
async def get_item(
    item_id: str,
) -> dict:
    """Get a single item by ID.

    Args:
        item_id: The unique identifier of the item

    Returns:
        Item details
    """
    client = await get_client()
    try:
        return await client.get_item(item_id)
    except ExampleAPIError as e:
        logger.warning("get_item failed: %s", e)
        raise ToolError(str(e)) from e


# ============================================================================
# Resources
# ============================================================================


@mcp.resource("skill://example/usage")
def skill_usage() -> str:
    """Usage guide for the Example MCP server tools."""
    return SKILL_CONTENT


# ============================================================================
# Entrypoints
# ============================================================================

# ASGI app for HTTP deployment (uvicorn mcp_example.server:app)
app = mcp.http_app()

# Stdio entrypoint for Claude Desktop / mpak
if __name__ == "__main__":
    logger.info("Running in stdio mode")
    mcp.run()
