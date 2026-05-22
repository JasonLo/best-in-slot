# pydantic-settings

**Slot**: Typed config loader from environment, `.env`, and other sources.

## Why pydantic-settings

It's `pydantic` + env-var loading + `.env` parsing + secrets dirs in one. Replaces hand-rolled `os.environ.get(...) or default` plumbing with a real schema and validation.

## Conventions

- One `Settings` class per service, in `<pkg>/settings.py`.
- Field defaults are documentation; surface required fields by having NO default.
- Provide an `lru_cache`'d factory `get_settings()` so FastAPI can `Depends(get_settings)`.
- Use `SettingsConfigDict(env_file=".env", env_prefix="MYAPP_")` to namespace env vars.
- Secrets via `secrets_dir` (e.g. `/run/secrets/`) when running in Docker / k8s.

## Alternatives considered

- **python-dotenv alone** — loads env vars but no typing, no validation. Use only when you genuinely just need that.
- **dynaconf** — heavier; prefer pydantic-settings unless you need multi-file layered configs.

## Gotchas

- Field types matter — `bool` from env coerces `"0"`, `"false"`, `"no"` to `False` (case-insensitive). Good.
- Nested settings via `__` delimiter: `MYAPP_DB__URL` → `Settings.db.url`.
- Don't read env vars manually elsewhere; if a value matters, put it on `Settings`.
