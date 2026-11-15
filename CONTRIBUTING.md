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

### Recommended Claude Code Skills

These skills automate common development tasks:

```bash
npx skills add nimblebraininc/skills --skill contributor --agent claude-code -y
npx skills add nimblebraininc/skills --skill mcpb --agent claude-code -y
```

## Development Workflow

### Adding a New Tool

1. **Add response models** to `src/mcp_example/api_models.py`
2. **Add client methods** to `src/mcp_example/api_client.py`
3. **Add the tool** to `src/mcp_example/server.py` using `@mcp.tool(annotations=...)`
4. **Describe the tool** in `src/mcp_example/skills/example/SKILL.md`
5. **Add tests** to `tests/`, run on both protocol versions
6. **Run checks**: `make check`

### Tool Design Guidelines

- One tool per API operation (`list_items`, `get_item`, `create_item`)
- Clear docstrings with Args/Returns sections
- Annotate every tool with `READS`, `ADDS` or `CHANGES` from `nimblebrain_server_sdk`
- Report a failure the caller must see by returning `to_tool_error(ServiceError(ErrorCode.X, "..."))` (from `nimblebrain_server_sdk.errors`) with a message safe to show, and log diagnostics to stderr with the `logging` module. See the [errors guide](https://docs.nimblebrain.ai/server-sdk/errors/). Do not send logs to the client (`ctx.info`, `ctx.error`): MCP's logging capability is deprecated as of the 2026-07-28 protocol (SEP-2577)
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
5. CI must pass (lint, typecheck, test, bundle)

### PR Checklist

- [ ] All new tools have docstrings with Args/Returns
- [ ] Pydantic models added for API responses
- [ ] Tests added for new functionality
- [ ] `make check` passes locally
- [ ] No hardcoded secrets or API keys

## Definition of Done

### For MCP Servers
- 5+ tools implemented
- manifest.json valid (v0.4)
- 5+ tests passing
- CI/CD workflow passing
- MTF scanner passes (no critical/high findings)

### For Companion Skills
- A directory under `src/mcp_example/skills/` named after the skill, holding a `SKILL.md` whose frontmatter has that `name` and a `description`, registered with `add_skills`
- Composes 2+ tools into a workflow
- At least 2 usage examples
