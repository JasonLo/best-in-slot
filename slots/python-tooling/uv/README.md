# uv

**Slot**: Python package manager + resolver + Python installer + script runner.

## Why uv

One tool replaces `pip`, `pip-tools`, `pipx`, `virtualenv`, `pyenv`, and most of `poetry`. Resolves in milliseconds, locks reproducibly, installs Python versions on demand, and ships an OCI base image (`ghcr.io/astral-sh/uv`) that's the canonical way to put modern Python in Docker.

Use everywhere. No conda unless you actually need conda-forge (then use [pixi](../../infra/pixi/)).

## Conventions

- Build backend: `uv_build` (Astral's own — not `hatchling`, not `setuptools`).
- `pyproject.toml` is the single source of truth; no `setup.py`, no `requirements.txt`.
- Flat package layout (`mypkg/` at repo root, not `src/mypkg/`).
- Lockfile (`uv.lock`) is committed.
- Run anything with `uv run …` — no manual venv activation.
- Install CLIs globally with `uv tool install <pkg>` or directly from git: `uv tool install git+https://github.com/jasonlo/<repo>`.
- Pin Python with `.python-version` (one line, e.g. `3.14`).

## Alternatives considered

- **poetry** — slower, more ceremony, no Python installer.
- **pip + venv** — fine but reinvents wheels for every project.
- **pixi** — keep for HPC / CUDA / conda-forge only.

## Gotchas

- For PyTorch with CUDA, add a `[tool.uv.sources]` block pointing to the right pytorch index (see `python-ai/pytorch`).
- `uv sync --frozen` in CI; never resolve in CI.
- `uv tool install` puts CLIs in `~/.local/bin` — ensure it's on `PATH`.
