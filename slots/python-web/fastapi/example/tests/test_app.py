from fastapi.testclient import TestClient

from fastapi_example.main import app


def test_health() -> None:
    with TestClient(app) as c:
        r = c.get("/healthz")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


def test_hello() -> None:
    with TestClient(app) as c:
        r = c.post("/hello", json={"name": "world"})
        assert r.status_code == 200
        assert r.json() == {"msg": "hello, world"}
