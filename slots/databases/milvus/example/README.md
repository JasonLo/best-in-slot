# milvus example

Uses **Milvus Lite** (file-backed, zero-install) so the test runs without a server.

```sh
uv sync
uv run pytest
```

For a real server:

```sh
curl -sLO https://github.com/milvus-io/milvus/releases/latest/download/milvus-standalone-docker-compose.yml
docker compose -f milvus-standalone-docker-compose.yml up -d
# point the client at "http://localhost:19530"
```
