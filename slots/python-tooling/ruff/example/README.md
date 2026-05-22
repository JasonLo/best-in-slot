# ruff example

```sh
uv sync
uv run ruff check .
uv run ruff format --check .
```

Then deliberately break a rule (add `import os` you don't use) and re-run to see the fix:

```sh
uv run ruff check --fix .
```
