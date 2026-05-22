# python-dotenv

**Slot**: Load `.env` files into `os.environ` for scripts and tools that don't (yet) use [pydantic-settings](../pydantic-settings/).

## Why python-dotenv

Smallest, oldest, most-installed `.env` loader. Use when you just need `os.environ.get("FOO")` to work in dev and you don't want a settings schema.

## Conventions

- `.env` lives at repo root and is **gitignored**.
- Commit `.env.example` showing the variable names (no values).
- Call `load_dotenv()` once at the top of entry-point scripts. Library code reads `os.environ` only.
- For anything that has structure / types, graduate to [pydantic-settings](../pydantic-settings/).

## Alternatives considered

- **pydantic-settings** — recommended when you have more than ~3 settings or any of them have types.
- **direnv** — shell-level, machine-wide; useful for personal dev shells, not for shipping.

## Gotchas

- `load_dotenv()` only sets vars that aren't already in the environment unless you pass `override=True`.
- Values are always strings — coerce on read.
- Don't import `dotenv` in libraries; libraries read `os.environ`.
