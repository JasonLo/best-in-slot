# postgres + psycopg (v3)

**Slot**: Relational database driver. Postgres is the database; psycopg v3 is the driver.

## Why psycopg (v3)

`psycopg` (the third-generation driver) is async-native, has connection pooling baked in, and supports binary protocol for performance. Replaces `psycopg2-binary`.

## Conventions

- Use `psycopg[binary]` for ease (precompiled wheels); `psycopg[c]` only when you want libpq from system.
- Connection string in env: `DATABASE_URL=postgresql://user:pass@host/db`.
- Use a **connection pool** (`psycopg_pool.AsyncConnectionPool`) for any service that handles >1 request.
- One query function per operation; pass `cur` or `conn` in — don't open connections inside helpers.
- For schema migrations: `alembic` if SQLAlchemy is already in the project; else plain SQL files in `migrations/` applied by a script.
- For ORM you usually don't need one. If you do: **sqlmodel** (pydantic + sqlalchemy) matches the project's Pydantic style (`pelican-data-loader` precedent).
- For tiny single-process apps: **Turso** (libsql) is fine (`ospo-stats` precedent). Postgres is the default for anything multi-user.

## Alternatives considered

- **psycopg2** — legacy, no async, slower.
- **asyncpg** — fastest async driver but lower-level; psycopg3 is now competitive and the API surface is friendlier.
- **SQLAlchemy core/ORM** — use when you need migrations + multiple drivers; otherwise it's overkill.

## Gotchas

- `psycopg.Connection` ≠ `psycopg.AsyncConnection`. Pick one model and stick with it per service.
- For pgvector, install `pgvector` extension + `psycopg[binary]` works directly: register `pgvector.psycopg.register_vector(conn)`.
- Parameter style is `%s` (libpq-style), not `?`. Mixing them up silently fails or returns 0 rows.
