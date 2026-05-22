# ruff cheatsheet

## Commands

```sh
ruff check .                 # lint
ruff check --fix .           # lint + auto-fix
ruff check --fix --unsafe-fixes .
ruff format .                # format (write)
ruff format --check .        # CI: fail if not formatted
ruff rule F401               # show rule details
ruff linter                  # list available linters
uvx ruff check               # run via uv (no install)
```

## `pyproject.toml` block

```toml
[tool.ruff]
target-version = "py314"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "RUF"]
ignore = ["E501"]            # line-length handled by formatter

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]         # allow asserts in tests

[tool.ruff.format]
quote-style = "double"
```

## In-line escapes

```python
import os  # noqa: F401  - imported for side effects
```

## Pre-commit hook

```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.8.4
  hooks:
    - id: ruff
      args: [--fix]
    - id: ruff-format
```
