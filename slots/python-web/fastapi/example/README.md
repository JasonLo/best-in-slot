# fastapi example

```sh
uv sync
uv run pytest                         # run tests
uv run fastapi dev fastapi_example/main.py   # serve on http://127.0.0.1:8000
# in another shell:
curl http://127.0.0.1:8000/healthz
curl -X POST http://127.0.0.1:8000/hello -H 'content-type: application/json' -d '{"name":"jason"}'
```
