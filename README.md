# This template is retired

It is kept read-only for reference. It is not maintained, and it packages servers as
desktop bundles, which is not how NimbleBrain servers ship.

To build an MCP server, start from a server that is maintained and in production:

- **[NimbleBrainInc/todosforagents](https://github.com/NimbleBrainInc/todosforagents)**: a
  FastMCP server on `nimblebrain-server-sdk` with annotated tools, the error contract, a
  server-published skill, keyset paging, a Postgres or SQLite store, and golden records of
  its advertised surface.
- **[NimbleBrainInc/mcp-careers](https://github.com/NimbleBrainInc/mcp-careers)**: a small
  stateless remote server, shipped as a container: `uv.lock` enforced in CI and the image,
  digest-pinned images, build and push on merge, promote-by-retag releases, and a golden
  record of its surface.

The `mcp-server` skill in
[NimbleBrainInc/skills](https://github.com/NimbleBrainInc/skills) walks through designing,
building and reviewing a server.
