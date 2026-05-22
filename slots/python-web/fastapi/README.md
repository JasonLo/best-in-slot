# fastapi

**Slot**: Python HTTP server (REST APIs, MCP HTTP transport, RAG backends).

## Why fastapi

Pydantic-native, async-first, automatic OpenAPI, and the ecosystem (uvicorn, starlette, dependency injection) is mature. `fastapi[standard]` pulls in everything you actually need.

## Conventions

- Install `fastapi[standard]` (gives you uvicorn, httptools, etc.).
- App lives in `<pkg>/main.py` exposing `app = FastAPI(...)`.
- Settings via [pydantic-settings](../pydantic-settings/) (NOT raw `os.environ`).
- Health endpoint at `/healthz` returning `{"status": "ok"}` — kubernetes / Docker / Traefik expect it.
- Validation via [pydantic](../pydantic/) request/response models.
- Use `Depends()` for cross-cutting concerns (DB session, auth, settings).
- Long-running ops → async; use [httpx](../httpx/) for outbound calls.
- One router per resource: `app.include_router(users.router, prefix="/users")`.

## Alternatives considered

- **flask** — sync-default, no built-in pydantic, no OpenAPI generation. Use only when adding to an existing flask app.
- **litestar** — fine, smaller ecosystem.
- **starlette directly** — for very small services prefer Hono+Bun ([web-ts/hono](../../web-ts/hono/)).

## Gotchas

- `fastapi[standard]` already pins `uvicorn[standard]`; don't double-declare.
- Default `uvicorn` reload watches the whole tree; use `--reload-dir` to narrow.
- Don't ship `--reload` in Docker. Bake a fixed `CMD` (`uvicorn app.main:app --host 0.0.0.0 --port 8000`).
- For RAG / vector search, see [databases/milvus](../../databases/milvus/) and the recipe in the root README.
