# ruff

**Slot**: Python linter and formatter (replaces black, isort, flake8, pyupgrade, autoflake).

## Why ruff

One tool, written in Rust, ~100× faster than the alternatives. Both linter (`ruff check`) and formatter (`ruff format`). Reads config from `pyproject.toml`. No plugin ecosystem to babysit.

## Conventions

- Single config block in `pyproject.toml` under `[tool.ruff]`.
- Target the same Python version as the project (`target-version = "py314"`).
- Enable a sensible default ruleset (`E`, `F`, `I`, `B`, `UP`, `SIM`); add `D` only if you write docstrings.
- Run `ruff check --fix` and `ruff format` together in pre-commit and CI.
- Don't disable rules globally — narrow them with `# noqa: <code>` at the call site.

## Alternatives considered

- **black + isort + flake8** — three tools where one works.
- **pylint** — too slow, too opinionated.

## Gotchas

- `ruff format` is *not* identical to `black` for every edge case (trailing commas, parentheses around return). Stay on ruff for both and there's nothing to reconcile.
- `select` is the allowlist; add codes you want, don't try to subtract from "all".
- Update ruff often — rules and fixes improve weekly.
