# fastapi cheatsheet

## Commands

```sh
uv add "fastapi[standard]"
uv run fastapi dev app/main.py        # auto-reload (dev)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000   # prod
```

## Minimal app

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI(title="my-service")


class Hello(BaseModel):
    name: str


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/hello")
def hello(body: Hello) -> dict[str, str]:
    return {"msg": f"hello, {body.name}"}
```

## With settings (pydantic-settings)

```python
from functools import lru_cache
from fastapi import Depends
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_url: str = "sqlite:///./app.db"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


@app.get("/whoami")
def whoami(s: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"db": s.db_url}
```

## Test (with httpx)

```python
from fastapi.testclient import TestClient
from app.main import app

def test_health() -> None:
    with TestClient(app) as c:
        r = c.get("/healthz")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
```

## Docker

See `slots/infra/docker/example/` — uses `ghcr.io/astral-sh/uv` base image.
