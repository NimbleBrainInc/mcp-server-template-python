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
npx skills add nimblebraininc/skills --skill mcpb --agent claude-code -y

# 2. Create repo from template
gh repo create NimbleBrainInc/mcp-<name> --template NimbleBrainInc/mcp-server-template --public --clone

# 3. Run /mcpb — scaffolds the server, implements tools, validates the
#    bundle (MTF scan), and authors companion skills, end to end

# 4. Iterate with `make check` as you build
```

## Definition of Done

- [ ] 5+ tools implemented
- [ ] manifest.json valid (v0.4)
- [ ] 5+ tests passing
- [ ] CI passing
- [ ] MTF scanner passes
- [ ] 2+ companion skills validated
- [ ] PR submitted and reviewed
