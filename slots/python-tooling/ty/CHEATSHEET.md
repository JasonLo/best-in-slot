# ty cheatsheet

## Commands

```sh
uv run ty check              # check the project
uv run ty check path/to/file.py
uv run ty --help
uvx ty check                 # no install
```

## `pyproject.toml` block

```toml
[dependency-groups]
dev = ["ty"]

[tool.ty]
# minimal: ty auto-discovers from project config
# pin python:
# python-version = "3.14"
```

## In-line escape (rare; prefer fixing the type)

```python
x: int = some_func()  # ty: ignore[invalid-assignment]
```

## CI step

```yaml
- run: uv run ty check
```
