# psycopg example

```sh
uv sync
uv run pytest                  # sanity check (psycopg imports)

# real Postgres (run a local one):
docker run -d --name pg-example -p 5433:5432 -e POSTGRES_PASSWORD=dev postgres:16
DATABASE_URL=postgresql://postgres:dev@localhost:5433/postgres uv run pytest -q
docker rm -f pg-example
```
