# Example MCP Server

MCP server providing Example API functionality via FastMCP.

## Architecture

```
src/mcp_example/
├── server.py      # MCP tools (FastMCP) + entrypoints
├── api_client.py  # Async HTTP client for Example API
├── api_models.py  # Pydantic models for API responses
└── skills/
    └── example/
        └── SKILL.md  # The skill served at skill://example/SKILL.md
```

## Server SDK

The server is built on `nimblebrain-server-sdk` ([quickstart](https://docs.nimblebrain.ai/server-sdk/quickstart/)).
Use it instead of writing these by hand:

- **Annotations**: every tool carries `READS`, `ADDS` or `CHANGES` (`@mcp.tool(annotations=READS)`). A tool with none reads to a client as a destructive write.
- **Errors**: a tool reports a failure by raising `ServiceError(ErrorCode.X, "...")` from `nimblebrain_server_sdk.errors`. `add_error_contract(mcp)`, called once where the server is built, returns it to the caller as an error result with its code. Never return a dict that describes an error (a host and a model score it as a success), and never raise `ValueError` for a caller's mistake. Classify an API failure with `ServiceError.from_upstream(status, detail=...)`; the API's own text goes in `detail` (logged), never in the message. ([Errors](https://docs.nimblebrain.ai/server-sdk/errors/))
- **Skills**: a skill is a directory under `skills/` whose name equals the `name` in its `SKILL.md` frontmatter, registered in the one `add_skills(mcp, [...])` call. Do not serve a `skill://` resource by hand. ([Skills](https://docs.nimblebrain.ai/server-sdk/skills/))
- **Listings**: a listing tool builds each row with `listing_row`, with a `uri` and a preview in place of any unbounded text field. The `uri` must resolve: a resource template (`example://items/{item_id}`) returns the whole record.
- **Tests**: run each test that crosses the wire on both protocol versions (`Client(mcp, mode="auto")` and `mode="legacy"`), annotate the parametrized `mode` with `Mode` from `nimblebrain_server_sdk.testing`, check skills with `served_skills` and listing rows with `assert_bounded_rows`. ([Testing](https://docs.nimblebrain.ai/server-sdk/testing/))

## Critical

- Package name: `@nimblebraininc/example` (npm-style scope, matches GitHub org)
- Manifest uses module execution: `python -m mcp_example.server`
- Server needs both entrypoints:
  ```python
  app = mcp.http_app()  # HTTP deployment
  if __name__ == "__main__":
      mcp.run()  # Stdio for Claude Desktop / mpak
  ```
- All logs to stderr (stdout is reserved for JSON-RPC)
- A failure the caller must see is a raised `ServiceError`; never log to the client with `ctx.info`/`ctx.error` (MCP's logging capability is deprecated as of 2026-07-28, SEP-2577)

## user_config

API key configured via manifest `user_config`, not hardcoded:
```json
{
  "user_config": {
    "api_key": {
      "type": "string",
      "sensitive": true,
      "required": true
    }
  },
  "server": {
    "mcp_config": {
      "env": { "EXAMPLE_API_KEY": "${user_config.api_key}" }
    }
  }
}
```

## Tooling

- **Package manager**: uv (not pip)
- **Linting/formatting**: ruff (not flake8, black, isort)
- **Type checking**: ty (not mypy, pyright)
- **Testing**: pytest with pytest-asyncio

## Commands

```bash
uv sync --dev               # Install dependencies
uv run ruff format src/ tests/   # Format
uv run ruff check src/ tests/    # Lint
uv run ty check src/             # Type check
uv run pytest tests/ -v          # Test
make check                       # All of the above
```

## Version Management

Version lives in four files that MUST stay in sync:

| File | Field |
|------|-------|
| `manifest.json` | `version` |
| `server.json` | `version` |
| `pyproject.toml` | `version` |
| `src/mcp_example/__init__.py` | `__version__` |

Bump all at once: `make bump VERSION=0.2.0`

## Releasing

```bash
make bump VERSION=0.2.0
git add -A && git commit -m "Bump version to 0.2.0"
git tag v0.2.0 && git push origin main v0.2.0
gh release create v0.2.0 --title "v0.2.0" --notes "- changelog"
```

GitHub Actions builds and uploads MCPB bundles automatically on release.

## Adding New Tools

1. Add response model to `api_models.py`
2. Add client method to `api_client.py`
3. Add `@mcp.tool(annotations=...)` function to `server.py`
4. Add a row for the tool to `skills/example/SKILL.md`
5. Add tests to `tests/`
6. Run `make check` to verify
