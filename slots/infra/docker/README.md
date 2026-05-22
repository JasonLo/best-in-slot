# docker

**Slot**: Container image build and runtime.

## Why docker (+ uv base image)

The canonical way to ship anything Python: `FROM ghcr.io/astral-sh/uv:python3.14-alpine` gives you a fast Python + uv in one layer. Multi-stage builds keep runtime images small.

## Conventions

- Base image: `ghcr.io/astral-sh/uv:python3.14-alpine` (or `-bookworm` if you need glibc / scientific wheels).
- Lock-first install: `COPY pyproject.toml uv.lock ./` and `uv sync --frozen --no-dev` before `COPY . .` so app-code changes don't bust the dep layer.
- Always set the uv envs that make Docker builds reproducible:
  ```
  ENV UV_COMPILE_BYTECODE=1
  ENV UV_LINK_MODE=copy
  ENV UV_PYTHON_DOWNLOADS=never  # uv:python images already have Python
  ```
- Run as non-root for any service that touches user data.
- `HEALTHCHECK` for any HTTP service (so Traefik / k8s know when to route traffic).
- Tag with both `latest` and the git SHA / version. Push to GHCR (`ghcr.io/jasonlo/<svc>`).

## Alternatives considered

- **distroless** — smaller but no shell; debugging hurts. Use only when image size really matters.
- **chainguard images** — security-focused; great if you're shipping to a regulated env.
- **`FROM python:3.x-slim`** — fine, but you re-implement uv install. The `uv` base image is one less layer.

## Gotchas

- Alpine + glibc-only wheels (pytorch, tensorflow, some scientific deps) → use `-bookworm` instead of `-alpine`.
- `--frozen` requires `uv.lock` to be committed and up-to-date.
- Don't `RUN apt-get install` in alpine — `apk add`.
- For dev, mount the source: `docker run -v $(pwd):/app …` and use `--reload`. Never ship `--reload`.
