# uv cheatsheet

## Project lifecycle

```sh
uv init --package mypkg        # new package project
uv add fastapi httpx           # runtime deps
uv add --dev pytest ruff ty    # dev deps
uv remove requests             # drop a dep
uv sync                        # install everything from lock
uv sync --frozen               # CI: fail if lock is stale
uv lock --upgrade              # bump everything
uv lock --upgrade-package httpx
```

## Run things

```sh
uv run python app.py
uv run pytest -q
uv run -m mypkg.main
uv run --with rich python      # one-off REPL with extra dep
```

## Python versions

```sh
uv python install 3.14
uv python list
echo 3.14 > .python-version
```

## Global tools

```sh
uv tool install ruff
uv tool install git+https://github.com/jasonlo/undock
uv tool list
uv tool upgrade --all
uv tool run black .            # ephemeral run, no install
uvx ruff check                 # alias for `uv tool run`
```

## Publishing

```sh
uv build                       # wheel + sdist in dist/
uv publish                     # to PyPI (uses UV_PUBLISH_TOKEN)
```

## Minimal `pyproject.toml`

```toml
[project]
name = "mypkg"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = ["httpx>=0.28"]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.8", "ty>=0.0.1a1"]

[project.scripts]
mypkg = "mypkg.cli:main"

[build-system]
requires = ["uv_build>=0.10"]
build-backend = "uv_build"

# Flat layout (package at repo root, not src/)
[tool.uv.build-backend]
module-root = ""
```

## CUDA index (PyTorch)

```toml
[tool.uv.sources]
torch = [{ index = "pytorch-cu128", marker = "sys_platform == 'linux'" }]

[[tool.uv.index]]
name = "pytorch-cu128"
url = "https://download.pytorch.org/whl/cu128"
explicit = true
```
