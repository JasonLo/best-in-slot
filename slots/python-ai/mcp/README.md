# mcp (Model Context Protocol)

**Slot**: Expose tools / resources / prompts to Claude Code, Claude Desktop, and other MCP-capable hosts. Matches `bear`'s `bear-mcp` entry point.

## Why mcp

A standardised JSON-RPC protocol the agent calls instead of bespoke HTTP. Same server works with Claude Code (`/mcp` add), Claude Desktop, Cursor, and others. Pick MCP over a custom FastAPI tool API when the consumer is an LLM agent.

Use FastAPI ([python-web/fastapi](../../python-web/fastapi/)) when the consumer is a human / a web client. Use both when you need both shapes (matches `bear`: `bear-api` + `bear-mcp`).

## Conventions

- Use the official `mcp` SDK (`mcp[cli]` for the dev tooling).
- Server lives in `<pkg>/mcp_server.py`; entrypoint via `[project.scripts]` (`my-mcp = "mypkg.mcp_server:main"`).
- Transport: **stdio** for local / Claude Code; **streamable HTTP** for hosted deployments.
- One file = one MCP "server"; group tools logically. Don't bundle unrelated tools in one server.
- Tool docstrings ARE the prompts — Claude sees them. Write them as instructions to a competent reader, not as Python docs.
- Validate inputs with [pydantic](../../python-web/pydantic/).
- Settings via [pydantic-settings](../../python-web/pydantic-settings/).

## Alternatives considered

- **Plain FastAPI tool API** — fine but every host needs custom wiring.
- **OpenAI function calling** — vendor-locked.
- **Skills / commands in a Claude Code plugin** ([claude-code/skill-md](../../claude-code/skill-md/)) — when the capability is *instructions*, not *code execution*. MCP runs code.

## Gotchas

- stdio servers communicate over stdin/stdout — `print()` from your code corrupts the protocol. Use stdlib `logging` to a file, or `stderr` only.
- Long-running tools should stream progress via the SDK's progress notifications, not block silently.
- For `claude mcp add` to work, the binary must be on `PATH` (use `uv tool install` or absolute path).
- Each tool call is independent; persist state via Resources (URIs) or an external store, not module globals.
