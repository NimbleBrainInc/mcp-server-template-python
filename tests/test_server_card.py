"""The Server Card a host reads before it connects, and the server.json that restates it.

The code is the one source of the server's metadata: the card is built from `FastMCP(...)`
and `add_server_card(...)`, and server.json, which an operator adds to a connectors catalog
and the MCP Registry lists, must say the same.
"""

import json
from pathlib import Path

import httpx2
from nimblebrain_server_sdk import SERVER_CARD_MEDIA_TYPE

from mcp_example import __version__
from mcp_example.server import mcp

SERVER_JSON = Path(__file__).parent.parent / "server.json"


async def served_card() -> dict:
    """Fetch the card the way a host does, from the streamable-HTTP app, in process."""
    transport = httpx2.ASGITransport(app=mcp.http_app())
    async with httpx2.AsyncClient(transport=transport, base_url="http://127.0.0.1") as http:
        response = await http.get("/mcp/server-card", headers={"accept": SERVER_CARD_MEDIA_TYPE})
    assert response.status_code == 200
    assert response.headers["content-type"] == SERVER_CARD_MEDIA_TYPE
    return response.json()


async def test_the_card_names_the_package_version():
    """Without `version=`, FastMCP would report its own version as the server's."""
    card = await served_card()
    assert card["version"] == __version__


async def test_server_json_agrees_with_the_card():
    card = await served_card()
    server_json = json.loads(SERVER_JSON.read_text())
    for field in ("name", "version", "title", "description"):
        assert server_json[field] == card[field], field
    # A connector has no placements, so neither carries a host block.
    assert "_meta" not in card
    assert "_meta" not in server_json
