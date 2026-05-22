# docker cheatsheet

## Build & run

```sh
docker build -t my-svc:dev .
docker run --rm -p 8000:8000 my-svc:dev
docker run --rm -it my-svc:dev sh      # debug
```

## Canonical Dockerfile (FastAPI / Streamlit / Gradio)

```dockerfile
# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS build

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=never

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

# ---------- runtime ----------
FROM python:3.14-slim AS runtime

ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY --from=build /app /app

RUN useradd -m -u 1000 app && chown -R app:app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -sf http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## .dockerignore

```
.git
.venv
__pycache__
*.pyc
.pytest_cache
.mypy_cache
.ruff_cache
.ty_cache
.env
*.log
```

## Publish to GHCR

```sh
docker tag my-svc:dev ghcr.io/jasonlo/my-svc:0.1.0
docker tag my-svc:dev ghcr.io/jasonlo/my-svc:latest
echo $GHCR_TOKEN | docker login ghcr.io -u jasonlo --password-stdin
docker push ghcr.io/jasonlo/my-svc:0.1.0
docker push ghcr.io/jasonlo/my-svc:latest
```

CI version of this lives in `slots/infra/github-actions/example/.github/workflows/publish.yml`.
