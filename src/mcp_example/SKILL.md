# Example MCP Server — Skill Guide

## Tools

| Tool | Use when... |
|------|-------------|
| `list_items` | You need to browse or search items |
| `get_item` | You have an item ID and need full details |

## Context Reuse

- Use the `id` from `list_items` results when calling `get_item`

## Workflows

### 1. Browse and Inspect
1. `list_items` with a limit to get an overview
2. For interesting items: `get_item` to get full details
