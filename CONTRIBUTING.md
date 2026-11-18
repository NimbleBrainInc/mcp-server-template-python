# Contributing

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (package manager)
- [ruff](https://docs.astral.sh/ruff/) (linting/formatting)
- [ty](https://github.com/astral-sh/ty) (type checking)
- [Docker](https://www.docker.com/) (for testing bundles)

### Setup

```bash
# Clone the repo
git clone https://github.com/NimbleBrainInc/mcp-example.git
cd mcp-example

# Install dependencies
uv sync --dev

# Run checks
make check
```

### Recommended Claude Code Skill

The `mcp-server` skill builds a server from this template end to end: it designs the tools
before code, implements them with `nimblebrain-server-sdk`, tests them, serves the server over
HTTP with its Server Card, and writes `server.json`. It also reviews an existing server's tools.

```bash
npx skills add nimblebraininc/skills --skill mcp-server --agent claude-code -y
```

## Development Workflow

### Adding a New Tool

Design the tool before writing it, the way the `mcp-server` skill does: a name and a
description that say when to call it, a `description` on every parameter, bounded results,
and one annotation. Then:

1. **Add response models** to `src/mcp_example/api_models.py`
2. **Add client methods** to `src/mcp_example/api_client.py`
3. **Add the tool** to `src/mcp_example/server.py` using `@mcp.tool(annotations=...)`
4. **Describe the tool** in `src/mcp_example/skills/example/SKILL.md`
5. **Add tests** to `tests/`, run on both protocol versions: the success path and each failure, checking the error code
6. **Run checks**: `make check`

### Tool Design Guidelines

- One tool per API operation (`list_items`, `get_item`, `create_item`)
- Clear docstrings with Args/Returns sections
- Annotate every tool with `READS` (reads and changes nothing), `ADDS` (writes without losing anything) or `CHANGES` (overwrites, removes, sends) from `nimblebrain_server_sdk`. A tool with no annotation reads to a host as a destructive write
- Report a failure the caller must see by raising `ServiceError(ErrorCode.X, "...")` (from `nimblebrain_server_sdk.errors`) with a message safe to show; `add_error_contract(mcp)` returns it to the caller as an error result. Never return an error as a plain dict: a host and a model score it as a success. Log diagnostics to stderr with the `logging` module. See the [errors guide](https://docs.nimblebrain.ai/server-sdk/errors/). Do not send logs to the client (`ctx.info`, `ctx.error`): MCP's logging capability is deprecated as of the 2026-07-28 protocol (SEP-2577)
- Return Pydantic models, not raw dicts

### Code Quality

All code must pass before merging:

```bash
uv run ruff format src/ tests/       # Format code
uv run ruff check src/ tests/        # Lint
uv run ty check src/                 # Type check
uv run pytest tests/ -v              # Run tests
```

Or simply: `make check`

## Pull Request Process

1. Create a branch from `main`
2. Make your changes
3. Run `make check` and fix any issues
4. Push and create a PR
5. CI must pass: the CI workflow (format, lint, typecheck, test, bundle) and the Security Scan workflow (`mpak-scanner` on the built bundle, failing on any critical or high finding)

### PR Checklist

- [ ] All new tools have docstrings with Args/Returns
- [ ] Pydantic models added for API responses
- [ ] Tests added for new functionality
- [ ] `make check` passes locally
- [ ] No hardcoded secrets or API keys

## Definition of Done

### For MCP Servers
- Tools designed with the `mcp-server` skill, each annotated and failing through the error contract
- Tests for each tool's success and failure paths, on both protocol versions
- `server.json` names the deployed URL and agrees with the Server Card (`tests/test_server_card.py`)
- The CI workflow passes: format, lint, typecheck, test, and `mcpb pack` (which validates `manifest.json`)
- The Security Scan workflow passes: no critical or high `mpak-scanner` findings

### For Companion Skills
- A directory under `src/mcp_example/skills/` named after the skill, holding a `SKILL.md` whose frontmatter has that `name` and a `description`, registered with `add_skills`
- Composes 2+ tools into a workflow
- At least 2 usage examples
