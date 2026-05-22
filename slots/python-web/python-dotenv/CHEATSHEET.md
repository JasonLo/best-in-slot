# python-dotenv cheatsheet

## Load

```python
from dotenv import load_dotenv
load_dotenv()                       # repo-root .env, no override
load_dotenv(override=True)          # overwrite existing env vars
load_dotenv("/path/to/.env.prod")
```

## Read (after load)

```python
import os
DB_URL = os.environ["DB_URL"]                  # required
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
```

## `.env.example` (commit this)

```
DB_URL=postgresql://user:pass@host/db
API_KEY=
DEBUG=false
```

## `.gitignore`

```
.env
.env.*
!.env.example
```

## Test isolation

```python
def test_with_env(monkeypatch):
    monkeypatch.setenv("DB_URL", "sqlite:///:memory:")
    ...
```
