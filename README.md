# best-in-slot

Personal tool selections, one per slot. Each folder under `slots/` documents a single decision point (package manager, vector DB, etc.) with exactly one recommended tool, a one-page best-practices doc, a one-page cheatsheet, and the smallest possible runnable example.

Compose à la carte — recipes near the bottom show common combinations.

## Getting started

```bash
uv sync                         # install pinned deps
uv run bis init            # interactive: mine → confirm structure → walk (per-slot picks)
uv run bis init mine       # mine + propose only — persists to slots/.bootstrap.yaml (US5)
uv run bis init walk       # fast local walk-through (arrow keys + Enter, powered by questionary); also runs the confirm step unless `--skip-confirm`
```

`bis init` now confirms the proposed slot **structure** before per-slot picks (US6) — you see a one-shot overview (categories, types, members, suggested splits) and can either accept (Enter) or `reshape` to split/merge/rename/drop/add slots in a single inner loop, no code edits to `bis/categories.py` needed.

The two-step `mine` / `walk` flow is what `/bis-bootstrap` uses under the hood: the LLM handles mining once, then hands off to the local CLI for snappy per-slot picks — no LLM in the loop during the walk. In Claude Code, the same flow is available conversationally via `/bis-bootstrap`. See `specs/001-bootstrap-discovery/quickstart.md` for the full first-run guide (existing-state handling, abort/resume, privacy verification, troubleshooting).

## Shared conventions (Python)

These hold across every Python slot unless the slot's README says otherwise:

- **Package manager**: `uv` with `uv_build` backend.
- **Python**: 3.14 (single floor across new code and shared libraries).
- **Lint / format**: `ruff`.
- **Type check**: `ty`.
- **Tests**: `pytest` (+ `pytest-asyncio` when async).
- **Layout**: flat package at repo root (not `src/`).
- **Config**: `.env` via `python-dotenv` or `pydantic-settings`.
- **Entry points**: `[project.scripts]` in `pyproject.toml`.

## Slot index

### python-tooling

| Slot | Tool | Use when |
|---|---|---|
| [package-manager](slots/python-tooling/uv/) | **uv** | Always — universal Python launcher and resolver |
| [linter-formatter](slots/python-tooling/ruff/) | **ruff** | Always — lint + format in one tool |
| [type-checker](slots/python-tooling/ty/) | **ty** | Always — fast Astral type checker |
| [test-runner](slots/python-tooling/pytest/) | **pytest** | Any tests, sync or async |
| [notebook-kernel](slots/python-tooling/ipykernel/) | **ipykernel** | Running notebooks in any editor |

### python-web

| Slot | Tool | Use when |
|---|---|---|
| [http-server](slots/python-web/fastapi/) | **fastapi[standard]** | HTTP API, MCP server, RAG backend |
| [data-app](slots/python-web/streamlit/) | **streamlit** | Dashboards, internal data apps |
| [ml-demo-ui](slots/python-web/gradio/) | **gradio** | ML model playground / TTS / vision demos |
| [http-client](slots/python-web/httpx/) | **httpx** | Outbound HTTP (sync or async) |
| [data-validation](slots/python-web/pydantic/) | **pydantic** | Validate inputs at boundaries |
| [config-loader](slots/python-web/pydantic-settings/) | **pydantic-settings** | Typed config from env + files |
| [env-file-loader](slots/python-web/python-dotenv/) | **python-dotenv** | Just need `.env` → `os.environ` |

### python-terminal

| Slot | Tool | Use when |
|---|---|---|
| [tui-framework](slots/python-terminal/textual/) | **textual** | Full-screen interactive terminal app |
| [cli-parser-typed](slots/python-terminal/typer/) | **typer** | Pydantic-heavy CLI, LLM agents, rich help |
| [cli-parser-stdlib](slots/python-terminal/argparse/) | **argparse** | Zero-dep simple CLI |

### python-data

| Slot | Tool | Use when |
|---|---|---|
| [dataframes](slots/python-data/pandas/) | **pandas** | Tabular data, ETL, EDA |
| [arrays](slots/python-data/numpy/) | **numpy** | Numeric arrays, vectorised math |
| [plotting](slots/python-data/altair/) | **altair** | Declarative interactive plots |
| [ml-datasets](slots/python-data/huggingface-datasets/) | **huggingface `datasets`** | Load / stream ML data |
| [notebook](slots/python-data/jupyter/) | **jupyter** | Exploratory work |

### python-ai

| Slot | Tool | Use when |
|---|---|---|
| [ml-framework](slots/python-ai/pytorch/) | **pytorch** | Train or fine-tune models |
| [model-zoo](slots/python-ai/transformers/) | **transformers** | Use pretrained HF models |
| [llm-sdk](slots/python-ai/anthropic-sdk/) | **anthropic** | Call Claude (OpenAI noted as alt) |
| [mcp-server](slots/python-ai/fastmcp/) | **fastmcp** | Expose tools to Claude Code / hosts |

### databases

| Slot | Tool | Use when |
|---|---|---|
| [relational](slots/databases/postgres-psycopg/) | **psycopg** (v3) on Postgres | Anything relational |
| [vector](slots/databases/milvus/) | **milvus** (`pymilvus`) | Dedicated vector DB at scale |
| [time-series](slots/databases/influxdb/) | **influxdb** | Metrics, sensors, time-series |

### infra

| Slot | Tool | Use when |
|---|---|---|
| [container](slots/infra/docker/) | **docker** (uv base image) | Ship any service |
| [hpc-env](slots/infra/pixi/) | **pixi** | CUDA / conda-forge deps, HPC |
| [batch-scheduler](slots/infra/htcondor/) | **htcondor** | GPU batch jobs on CHTC |
| [ci](slots/infra/github-actions/) | **github-actions** + `setup-uv@v7` | Run CI |

### docs

| Slot | Tool | Use when |
|---|---|---|
| [docs-site](slots/docs/mkdocs-material/) | **mkdocs-material** | Project / API docs |

### web-ts

| Slot | Tool | Use when |
|---|---|---|
| [static-site](slots/web-ts/astro/) | **astro@^6** | Personal site, blog, marketing |
| [ts-runtime](slots/web-ts/bun/) | **bun** | Run / package TS without Node |
| [ts-web-framework](slots/web-ts/hono/) | **hono** | Tiny TS HTTP service |
| [markdown-renderer](slots/web-ts/markdown-it/) | **markdown-it** | Render Markdown to HTML |

### claude-code

| Slot | Tool | Use when |
|---|---|---|
| [plugin-format](slots/claude-code/skill-md/) | **SKILL.md** | Author Claude Code skills / commands / agents |

## Recipes

| Recipe | Slots to combine |
|---|---|
| FastAPI service (HTTP + RAG) | uv, ruff, ty, pytest, fastapi, httpx, pydantic, pydantic-settings, python-dotenv, postgres-psycopg, milvus, docker, github-actions, mkdocs-material |
| Data app / dashboard | uv, ruff, ty, streamlit, pandas, altair, python-dotenv, docker |
| ML model demo | uv, gradio, transformers, pytorch, python-dotenv, docker |
| Textual TUI tool | uv, ruff, ty, pytest, textual, argparse, python-dotenv, github-actions |
| LLM CLI agent | uv, ruff, ty, pytest, typer, httpx, pydantic, python-dotenv, anthropic-sdk |
| PyTorch experiment | uv, ruff, ty, pytest, pytorch, transformers, pandas, numpy, altair, jupyter, ipykernel, huggingface-datasets |
| GPU batch on CHTC | pixi, docker, htcondor, github-actions |
| Static site | astro |
| Tiny TS HTTP service | bun, hono, markdown-it |
| Claude Code plugin | skill-md |
| MCP server | uv, fastmcp, pydantic, anthropic-sdk |
