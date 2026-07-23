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
# 1. Install development skills
npx skills add nimblebraininc/skills --skill build-mcp
npx skills add nimblebraininc/skills --skill validate-mcpb
npx skills add nimblebraininc/skills --skill author-skills-for-server

# 2. Create repo from template
gh repo create NimbleBrainInc/mcp-<name> --template NimbleBrainInc/mcp-server-template --public --clone

# 3. Use /build-mcp to scaffold, or start from the template code

# 4. Implement tools, run make check

# 5. Validate bundle with /validate-mcpb

# 6. Author companion skills with /author-skills-for-server
```

## Definition of Done

- [ ] 5+ tools implemented
- [ ] manifest.json valid (v0.4)
- [ ] 5+ tests passing
- [ ] CI passing
- [ ] MTF scanner passes
- [ ] 2+ companion skills validated
- [ ] PR submitted and reviewed
