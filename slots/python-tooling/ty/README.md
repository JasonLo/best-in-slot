# ty

**Slot**: Python type checker.

## Why ty

Astral's type checker (the same shop behind uv and ruff). Written in Rust, designed to be a drop-in alternative to mypy / pyright with a simpler config and dramatically lower runtime. Integrates with uv as a dev dep.

> Note: `ty` is pre-1.0; APIs and rules can change. It's stable enough for personal use and for `code-template`. If you're shipping a library to many consumers, pin the version.

## Conventions

- Add as `[dependency-groups].dev`.
- Run `uv run ty check` locally and in CI.
- Don't sprinkle `# type: ignore` — fix the type or narrow the value at the boundary.
- Use stdlib `typing` features (`|`, `Self`, `TypedDict`); avoid `typing_extensions` unless backporting.

## Alternatives considered

- **mypy** — slower; many plugin requirements (pydantic, sqlalchemy) once you have dataclasses everywhere.
- **pyright** — fast but Node-based and harder to drop into a pure-Python CI.

## Gotchas

- `ty` doesn't yet support every plugin mypy does. If you hit a real wall, fall back to pyright for one project — don't paper over it.
- Pin a known-good version (`ty==X.Y.Z`) in lockfiles since pre-1.0.
