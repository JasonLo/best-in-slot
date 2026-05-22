# mcp example

Minimal MCP server: 2 tools (`echo`, `add`) + 1 resource (`memo://<topic>`).

```sh
uv sync
uv run pytest                                # tools work as plain functions

uv run mcp-example                           # runs the stdio server (Ctrl-C to stop)

# Register with Claude Code:
claude mcp add mcp-example --command "$(pwd)/.venv/bin/mcp-example"
```
