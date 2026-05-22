# httpx cheatsheet

## Sync

```python
import httpx

with httpx.Client(timeout=10.0, base_url="https://api.example.com") as client:
    r = client.get("/users", params={"limit": 50})
    r.raise_for_status()
    data = r.json()
```

## Async

```python
import httpx

async def fetch() -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get("https://api.example.com/users")
        r.raise_for_status()
        return r.json()
```

## Retries with tenacity

```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
)
def fetch(client: httpx.Client, url: str) -> dict:
    r = client.get(url)
    r.raise_for_status()
    return r.json()
```

## Inside FastAPI (shared client)

```python
@app.on_event("startup")
async def startup() -> None:
    app.state.http = httpx.AsyncClient(timeout=10.0)

@app.on_event("shutdown")
async def shutdown() -> None:
    await app.state.http.aclose()
```

## Mocking with respx

```python
import respx, httpx

@respx.mock
def test_call():
    respx.get("https://api.example.com/u/1").respond(200, json={"id": 1})
    r = httpx.get("https://api.example.com/u/1")
    assert r.json() == {"id": 1}
```
