# Example MCP Server

An MCP (Model Context Protocol) server that provides access to the Example API, allowing AI assistants to interact with Example data.

## Features

- List and retrieve items from the Example API
- Async HTTP client with error handling
- Typed responses with Pydantic models
- Built on the [NimbleBrain server SDK](#built-on-the-nimblebrain-server-sdk): annotated tools, classified errors, a skill served to the host, and a Server Card

## Installation

### Using mpak (Recommended)

```bash
# Configure your API key
mpak config set @nimblebraininc/example api_key=your_api_key_here

# Run the server
mpak run @nimblebraininc/example
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/NimbleBrainInc/mcp-example.git
cd mcp-example

# Install dependencies with uv
uv sync

# Set your API key
export EXAMPLE_API_KEY=your_api_key_here

# Run the server
uv run python -m mcp_example.server
```

## Configuration

### Getting Your API Key

1. Go to https://example.com/settings/api
2. Create a new API key
3. Copy the key

### Claude Desktop Configuration

Add to your `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "example": {
      "command": "mpak",
      "args": ["run", "@nimblebraininc/example"]
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_items` | List items from the API with optional limit. Each row carries a `uri` and a preview of the description |
| `get_item` | Get a single item, whole, by its ID |

Both tools read and change nothing, and say so with the `READS` annotation. A row's `uri`
(`example://items/<id>`) is a resource that returns the whole item as JSON. The server also
serves one skill, `skill://example/SKILL.md`, which tells an agent when to use each tool.

## Built on the NimbleBrain server SDK

The server uses [`nimblebrain-server-sdk`](https://pypi.org/project/nimblebrain-server-sdk/)
for what every server on NimbleBrain shares. Start with the
[quickstart](https://docs.nimblebrain.ai/server-sdk/quickstart/).

| The server does this | With | Guide |
|---|---|---|
| Declares what each tool can change | `READS`, `ADDS`, `CHANGES` | [Quickstart](https://docs.nimblebrain.ai/server-sdk/quickstart/) |
| Returns a failure with a code the caller can act on | `add_error_contract`, `ServiceError`, `ErrorCode` | [Errors](https://docs.nimblebrain.ai/server-sdk/errors/) |
| Serves the skill in `src/mcp_example/skills/` | `add_skills` | [Skills](https://docs.nimblebrain.ai/server-sdk/skills/) |
| Names and describes itself to a host before it connects | `add_server_card` | [Server Card](https://docs.nimblebrain.ai/server-sdk/server-card/) |
| Tests what a host sees, on both protocol versions | `Mode`, `served_skills`, `assert_bounded_rows` | [Testing](https://docs.nimblebrain.ai/server-sdk/testing/) |

### A tool

A tool carries one annotation: `READS`, `ADDS` (a write that loses nothing) or `CHANGES` (a
write that overwrites or removes). It reports a failure by raising `ServiceError`, and
`add_error_contract`, called once where the server is built, returns it to the caller as an
error result. A tool never returns a dict that describes an error: a host and a model score
that as a success.

```python
from fastmcp import FastMCP
from nimblebrain_server_sdk import ADDS, add_error_contract
from nimblebrain_server_sdk.errors import ErrorCode, ServiceError

mcp = FastMCP("com.example/example", version="0.1.0")
add_error_contract(mcp)

ITEMS: dict[str, str] = {}


@mcp.tool(annotations=ADDS)
async def create_item(name: str) -> dict[str, str]:
    """Create an item and return it."""
    if not name.strip():
        raise ServiceError(ErrorCode.BAD_INPUT, "`name` is empty.")
    item_id = str(len(ITEMS) + 1)
    ITEMS[item_id] = name
    return {"id": item_id, "name": name}
```

The caller of `create_item` with an empty name receives an error result whose structured
content is `{"error": {"code": "bad_input", "retryable": false, "message": "`name` is empty."}}`.

### A skill

A skill is a directory that holds a `SKILL.md`. The frontmatter needs a `name` and a
`description`, and `name` must equal the directory's name. `add_skills` checks every skill
when the server is imported and serves each at `skill://<name>/SKILL.md`:

```python
from pathlib import Path

from fastmcp import FastMCP
from nimblebrain_server_sdk import add_skills

mcp = FastMCP("com.example/example", version="0.1.0")
add_skills(mcp, [Path("src/mcp_example/skills/example")])
```

### A test

A host connects on one of two protocol versions, so a test runs on both:
`Client(mcp, mode="auto")` negotiates 2026-07-28 and `mode="legacy"` runs the 2025-11-25
handshake. `Mode` is the type of that parameter. `served_skills` reads every skill file back
the way a host does.

```python
import pytest
from fastmcp import Client
from nimblebrain_server_sdk.testing import Mode, served_skills

from mcp_example.server import mcp


@pytest.mark.parametrize("mode", ["auto", "legacy"])
async def test_the_skill_is_served(mode: Mode) -> None:
    skills = await served_skills(mcp, mode)
    assert set(skills) == {"skill://example/SKILL.md"}


@pytest.mark.parametrize("mode", ["auto", "legacy"])
async def test_an_empty_item_id_is_bad_input(mode: Mode) -> None:
    async with Client(mcp, mode=mode) as client:
        result = await client.call_tool("get_item", {"item_id": " "}, raise_on_error=False)
    assert result.is_error
    assert result.structured_content["error"]["code"] == "bad_input"
```

`tests/test_server.py` holds the full set.

### A Server Card

A host that has only the server's URL reads its Server Card, at `<mcp-url>/server-card`,
to name and describe it before it connects. `name` and `version` come from the `FastMCP`
constructor, so the server is named in reverse-DNS form and given its own version (without
`version=`, FastMCP reports its own). `title` and `description` are 1 to 100 characters:

```python
from fastmcp import FastMCP
from nimblebrain_server_sdk import add_server_card

from mcp_example import __version__

mcp = FastMCP("com.example/example", version=__version__)
add_server_card(mcp, title="Example", description="List and read items from the Example API.")
```

The card is served over streamable HTTP only: `make run-http`, then
`curl -s http://127.0.0.1:8000/mcp/server-card`. This server is a connector, so the card has
no `placements`; an app's server passes them for its `ui://` views.

## Deploying: server.json

`server.json` is an [MCP Registry `ServerDetail`](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/generic-server-json.md):
what an operator adds to a deployed NimbleBrain's
[connectors catalog](https://docs.nimblebrain.ai/config/connectors-catalog/), and what
`mcp-publisher` lists on the official MCP Registry. It restates the card's `name`, `title`,
`description` and `version`, and adds `remotes`, the URL the server is deployed at. Replace
the placeholder `https://mcp.example.com/mcp` with yours. `tests/test_server_card.py` fails
when `server.json` and the served card disagree, and `make bump` moves both versions together.

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest tests/ -v

# Format code
uv run ruff format src/ tests/

# Lint
uv run ruff check src/ tests/

# Type check
uv run ty check src/

# Run all checks
make check

# Serve over HTTP at http://127.0.0.1:8000/mcp
make run-http
```

`make run-http` binds loopback. On Linux, a NimbleBrain running in Docker reaches the host
through the Docker bridge: `make run-http HOST=172.17.0.1`, or `HOST=0.0.0.0`, which also
exposes the server to the network.

## License

MIT
