# fastmcp example

Minimal FastMCP server: 2 tools (`echo`, `add`) + 1 resource (`memo://<topic>`).

```sh
uv sync
uv run pytest                                # exercised via in-memory fastmcp.Client

uv run fastmcp-example                       # runs the stdio server (Ctrl-C to stop)

# Register with Claude Code (either form works):
uv run fastmcp install claude-code fastmcp_example/server.py:mcp --server-name fastmcp-example
# or, after `uv tool install .`:
claude mcp add fastmcp-example --command "$(which fastmcp-example)"
```
