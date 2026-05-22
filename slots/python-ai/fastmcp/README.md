# fastmcp (Model Context Protocol server framework)

**Slot**: Expose tools / resources / prompts to Claude Code, Claude Desktop, and other MCP-capable hosts. Matches `bear`'s `bear-mcp` entry point.

## Why fastmcp

[`fastmcp`](https://github.com/jlowin/fastmcp) is the actively-maintained successor to FastMCP 1.0 (which was upstreamed into the official `mcp` SDK in 2024). It's the standard high-level framework for writing MCP servers in Python — Pythonic decorators, automatic schema generation from type hints, an in-memory testing client, and a CLI that wires servers into Claude Code / Cursor / Claude Desktop for you.

Pick MCP when the consumer is an LLM agent. Pick FastAPI ([python-web/fastapi](../../python-web/fastapi/)) when the consumer is a human / web client. Use both for a `bear`-style split (`bear-api` + `bear-mcp`).

## Conventions

- Install the standalone package: `fastmcp` (not `mcp[cli]`). It pulls the official `mcp` SDK in as a dependency.
- Server lives in `<pkg>/mcp_server.py`; entrypoint via `[project.scripts]` (`my-mcp = "mypkg.mcp_server:main"`).
- Construct the server as `mcp = FastMCP("my-mcp")`. Decorate with bare `@mcp.tool` / `@mcp.resource(...)` / `@mcp.prompt` — no parens, 2.x style.
- Transport: **stdio** for local / Claude Code; **streamable HTTP** (`transport="http"`) for hosted deployments.
- One file = one MCP "server"; group tools logically. Don't bundle unrelated tools in one server.
- Tool docstrings ARE the prompts — Claude sees them. Write them as instructions to a competent reader, not as Python docs.
- Validate inputs with [pydantic](../../python-web/pydantic/) (fastmcp accepts pydantic models as parameter types and derives the JSON schema from them).
- Settings via [pydantic-settings](../../python-web/pydantic-settings/).
- Test through the in-memory `fastmcp.Client(mcp)` (see CHEATSHEET) — `@mcp.tool` rebinds the symbol to a `FunctionTool`, so the decorated function is **not** callable directly.

## Alternatives considered

- **Official `mcp` SDK directly** — fine, but `fastmcp` is a superset (auth, OpenAPI generation, proxying, server composition, a real CLI) and is effectively where the high-level API is developed. Use the bare SDK only if you can't add the dep.
- **Plain FastAPI tool API** — fine but every host needs custom wiring.
- **OpenAI function calling** — vendor-locked.
- **Skills / commands in a Claude Code plugin** ([claude-code/skill-md](../../claude-code/skill-md/)) — when the capability is *instructions*, not *code execution*. MCP runs code.

## Gotchas

- stdio servers communicate over stdin/stdout — `print()` from your code corrupts the protocol. Use stdlib `logging` to a file, or `stderr` only.
- `@mcp.tool` returns a `FunctionTool`, not the wrapped function. In tests, call tools through `fastmcp.Client(mcp)` (in-memory, no subprocess) — don't invoke the decorated symbol directly.
- Long-running tools should stream progress through the `Context` parameter (`ctx.report_progress(...)`), not block silently.
- `claude mcp add` needs the binary on `PATH` (`uv tool install .` or an absolute path). `fastmcp install claude-code server.py` does the wiring for you.
- Each tool call is independent; persist state via Resources (URIs) or an external store, not module globals.
