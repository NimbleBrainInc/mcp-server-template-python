---
name: New MCP Server
about: Track implementation of a new MCP server
title: 'Add [SERVICE] MCP server'
labels: enhancement, mcp-server
assignees: ''
---

## Service

**Name:**
**API Docs:**
**Auth Method:** API Key / Bearer Token / OAuth

## Proposed Tools

| Tool | Description |
|------|-------------|
| `list_*` | |
| `get_*` | |
| `create_*` | |
| `update_*` | |
| `search_*` | |

## Suggested Companion Skills

1. **skill-name** - Description of the workflow
2. **skill-name** - Description of the workflow

## Getting Started

```bash
# 1. Install the build skill
npx skills add nimblebraininc/skills --skill mcp-server --agent claude-code -y

# 2. Create the repo from the template
gh repo create NimbleBrainInc/mcp-<name> --template NimbleBrainInc/mcp-server-template-python --public --clone

# 3. Ask your agent to build the server with the mcp-server skill: it proposes
#    the tools, implements and tests them, serves the server with its Server
#    Card, and writes server.json

# 4. Iterate with `make check` as you build
```

## Definition of Done

- [ ] Tools designed with the `mcp-server` skill, each annotated and failing through the error contract
- [ ] Tests for each tool's success and failure paths, on both protocol versions
- [ ] `server.json` names the deployed URL and agrees with the Server Card
- [ ] CI workflow passing (format, lint, typecheck, test, bundle)
- [ ] Security Scan workflow passing (no critical or high findings)
- [ ] Companion skills served with `add_skills`
- [ ] PR submitted and reviewed
