import httpx
import respx

from httpx_example.client import get_json


@respx.mock
def test_get_json_ok() -> None:
    respx.get("https://api.example.com/u/1").respond(200, json={"id": 1, "name": "j"})
    with httpx.Client(timeout=2.0) as c:
        assert get_json(c, "https://api.example.com/u/1") == {"id": 1, "name": "j"}


@respx.mock
def test_get_json_retries() -> None:
    route = respx.get("https://api.example.com/flaky")
    route.side_effect = [
        httpx.Response(500),
        httpx.Response(200, json={"ok": True}),
    ]
    with httpx.Client(timeout=2.0) as c:
        assert get_json(c, "https://api.example.com/flaky") == {"ok": True}
    assert route.call_count == 2
