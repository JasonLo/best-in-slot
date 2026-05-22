# pydantic-settings cheatsheet

## Basic

```python
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MYAPP_",
        extra="ignore",
    )

    db_url: str = "sqlite:///./app.db"
    api_key: str = Field(..., description="required")
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

`.env`:

```
MYAPP_DB_URL=postgresql://...
MYAPP_API_KEY=sk-...
MYAPP_DEBUG=true
```

## With FastAPI

```python
from fastapi import Depends, FastAPI

app = FastAPI()

@app.get("/whoami")
def whoami(s: Settings = Depends(get_settings)) -> dict:
    return {"db": s.db_url, "debug": s.debug}
```

## Nested

```python
class DBSettings(BaseSettings):
    url: str
    pool_size: int = 10

class Settings(BaseSettings):
    db: DBSettings
    model_config = SettingsConfigDict(env_nested_delimiter="__")

# env:  MYAPP_DB__URL=...   MYAPP_DB__POOL_SIZE=20
```
