# hono

**Slot**: Tiny TS web framework. Matches `md-render`'s setup.

## Why hono

Express-shaped but typed, tree-shakeable, runs on Bun / Node / Workers / Deno with the same code. Middleware story is small and explicit. Routes are typed end-to-end (request → response) when you use `@hono/zod-validator` or `hono/typed-request`.

Use hono when:
- The service is small (handful of endpoints).
- You want TS instead of Python.
- The deployment target is Bun or an edge runtime.

For Python services, [fastapi](../../python-web/fastapi/) wins.

## Conventions

- One `app.ts` exporting the `Hono` instance + `export default { fetch: app.fetch }` for runtime adapters.
- Validate inputs with `@hono/zod-validator` (zod schemas).
- Routes grouped by resource: `app.route("/users", users)`.
- Health endpoint at `/healthz`.
- For markdown rendering pair with [markdown-it](../markdown-it/) (the `md-render` recipe).
- Lockfile = `bun.lock` ([bun](../bun/) slot covers details).

## Alternatives considered

- **Express** — old, untyped, sync default.
- **Fastify** — typed, Node-only, slightly heavier than hono.
- **Itty router** — even tinier; lose middleware + validation conveniences.

## Gotchas

- `c.json(...)` infers the response type — keep handlers small so TS can do its job.
- `app.fetch` is the standard runtime entry — `bun --watch run` and Workers both consume it.
- Don't add `body-parser` etc.; hono's `c.req.json()` / `c.req.parseBody()` cover it.
- Middleware order matters — auth before validation before handler.
