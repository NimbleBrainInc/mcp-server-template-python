"""Example MCP Server - FastMCP Implementation.

This is a template server. Replace 'example' with your service name and
implement the tools for your API.

Getting started:
1. Rename this package from mcp_example to mcp_<yourservice>
2. Update manifest.json, server.json, pyproject.toml with your service info, and the
   server's name, TITLE and DESCRIPTION below (server.json restates them)
3. Implement your API client in api_client.py
4. Add Pydantic models in api_models.py
5. Add tools below using @mcp.tool(annotations=...)
6. Describe them in skills/example/SKILL.md (rename the directory and its `name` together)

The server is built on nimblebrain-server-sdk: tool annotations, the error contract and
skills come from it. Guide: https://docs.nimblebrain.ai/server-sdk/quickstart/
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ResourceError
from nimblebrain_server_sdk import (
    PREVIEW_CHARS,
    READS,
    add_error_contract,
    add_server_card,
    add_skills,
    listing_row,
)
from nimblebrain_server_sdk.errors import ErrorCode, ServiceError
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_example import __version__
from mcp_example.api_client import ExampleAPIError, ExampleClient

# Logging setup - all logs to stderr (stdout is reserved for JSON-RPC). Diagnostics go
# here, never to the client: MCP's logging capability is deprecated as of the 2026-07-28
# protocol (SEP-2577). A failure the caller must see is a raised ServiceError.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_example")

logger.info("Example server module loading...")

# Each skill is a directory holding a SKILL.md whose frontmatter `name` equals the
# directory's name. A skill is served at skill://<name>/SKILL.md.
SKILLS_DIR = Path(__file__).parent / "skills"

MAX_LIMIT = 100

# The Server Card's title and description, restated in server.json (a test holds them equal).
TITLE = "Example"
DESCRIPTION = "List and read items from the Example API."

# The name is reverse-DNS (the Server Card and the MCP Registry require it), and the version
# is the package's own: without `version=`, FastMCP reports its own version as the server's.
mcp = FastMCP(
    "com.example/example",
    version=__version__,
    instructions=(
        "Before using tools, read the skill://example/SKILL.md resource "
        "for tool selection guidance and workflow patterns."
    ),
)
# A ServiceError a tool raises reaches the caller as an error result with its code.
add_error_contract(mcp)
add_skills(mcp, [SKILLS_DIR / "example"])
# What a host reads, at <mcp-url>/server-card, before it connects. A connector has no
# placements; an app's server passes `placements=[...]` for its ui:// views.
add_server_card(mcp, title=TITLE, description=DESCRIPTION)

# Global client instance (lazy initialization)
_client: ExampleClient | None = None


async def get_client() -> ExampleClient:
    """Get or create the API client instance.

    Raises:
        ServiceError: when EXAMPLE_API_KEY is not set, so the caller sees why the tool failed.
    """
    global _client
    if _client is None:
        api_key = os.environ.get("EXAMPLE_API_KEY")
        if not api_key:
            raise ServiceError(
                ErrorCode.AUTH_REQUIRED,
                "EXAMPLE_API_KEY environment variable is required",
            )
        _client = ExampleClient(api_key=api_key)
    return _client


def upstream_error(error: ExampleAPIError) -> ServiceError:
    """Classify an Example API failure by its HTTP status.

    The caller receives the code, the status and a generic message. The API's own text
    may name internals, so it goes to `detail`, which is logged and never returned.
    """
    return ServiceError.from_upstream(error.status, detail=error.message)


# Health endpoint for HTTP transport
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for monitoring."""
    return JSONResponse({"status": "healthy", "service": "mcp-example"})


# ============================================================================
# Tools - Add your MCP tools below
#
# Every tool declares what a call can change: READS, ADDS (a write that loses
# nothing) or CHANGES (a write that overwrites or removes). A tool with no
# annotation reads to a client as a destructive write.
#
# A tool reports a failure by raising ServiceError, and add_error_contract returns
# it to the caller as an error result. Never return a dict that describes an error:
# a host and a model score it as a success.
# ============================================================================


@mcp.tool(annotations=READS)
async def list_items(
    limit: int = 20,
) -> list[dict[str, Any]]:
    """List items from the Example API.

    Args:
        limit: Maximum number of items to return (1-100, default 20)

    Returns:
        One row per item. A row carries the item's `uri` and a `description_preview`
        in place of the full description. `get_item`, or a read of the `uri`, returns
        the whole item.
    """
    if not 1 <= limit <= MAX_LIMIT:
        raise ServiceError(ErrorCode.BAD_INPUT, f"`limit` must be between 1 and {MAX_LIMIT}.")
    try:
        client = await get_client()
        items = await client.list_items(limit=limit)
    except ExampleAPIError as e:
        raise upstream_error(e) from e
    # A page holds many rows, so an unbounded field leaves each row as a preview.
    return [
        listing_row(
            {**item, "uri": f"example://items/{item['id']}"},
            preview={"description": PREVIEW_CHARS},
        )
        for item in items
    ]


async def read_item(item_id: str) -> dict[str, Any]:
    """Read one whole item, for the tool and the resource that both return it.

    Raises:
        ServiceError: classified, with a message safe to show the caller.
    """
    if not item_id.strip():
        raise ServiceError(ErrorCode.BAD_INPUT, "`item_id` is empty.")
    try:
        client = await get_client()
        return await client.get_item(item_id)
    except ExampleAPIError as e:
        raise upstream_error(e) from e


@mcp.tool(annotations=READS)
async def get_item(
    item_id: str,
) -> dict[str, Any]:
    """Get a single item by ID.

    Args:
        item_id: The unique identifier of the item

    Returns:
        Item details
    """
    return await read_item(item_id)


# ============================================================================
# Resources
# ============================================================================


# The address a `list_items` row carries in `uri`. A row is a summary, so its uri must
# read back the whole record.
@mcp.resource("example://items/{item_id}", name="item", mime_type="application/json")
async def item_resource(item_id: str) -> str:
    """One whole item, as JSON: the same record `get_item` returns."""
    try:
        return json.dumps(await read_item(item_id))
    except ServiceError as e:
        # add_error_contract covers tool calls. A resource read has no result to carry
        # the error envelope, so the failure is the read's error, with the same message
        # safe to show.
        raise ResourceError(e.message) from e


# ============================================================================
# Entrypoints
# ============================================================================

# ASGI app for HTTP deployment (uvicorn mcp_example.server:app)
app = mcp.http_app()

# Stdio entrypoint for Claude Desktop / mpak
if __name__ == "__main__":
    logger.info("Running in stdio mode")
    mcp.run()
