# httpx

**Slot**: Python HTTP client (sync + async).

## Why httpx

`requests`-compatible API with first-class async support, HTTP/2, connection pooling, and a great timeout/retry story. The right default for both scripts and FastAPI services.

## Conventions

- Use a `Client` (or `AsyncClient`) as a context manager — never one-shot `httpx.get()` in hot paths (pooling).
- Always set an explicit `timeout=` (default is 5s but be deliberate).
- Pair with **`tenacity`** for retries when you need exponential backoff on idempotent requests.
- Use `httpx.AsyncClient` inside FastAPI handlers; share it via a `Depends` factory or `app.state`.
- For testing, use `respx` to mock httpx routes without touching the network.

## Alternatives considered

- **requests** — sync only, abandoned-ish, no HTTP/2.
- **aiohttp** — async-only, no sync API, smaller user base now.
- **urllib3 / urllib** — stdlib but verbose.

## Gotchas

- `httpx.AsyncClient` is *not* thread-safe; use one per event loop.
- Default `follow_redirects=False` — set explicitly when you need them.
- For streaming downloads use `client.stream()` and iterate, don't call `.read()` on huge bodies.
