# psycopg cheatsheet

## Sync

```python
import psycopg

with psycopg.connect("postgresql://user:pass@host/db") as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT id, name FROM users WHERE active = %s", (True,))
        for row in cur:
            print(row)
```

## Async + pool

```python
from psycopg_pool import AsyncConnectionPool

pool = AsyncConnectionPool("postgresql://...", min_size=1, max_size=10)
await pool.open()

async with pool.connection() as conn:
    async with conn.cursor() as cur:
        await cur.execute("SELECT 1")
        print(await cur.fetchone())

await pool.close()
```

## With FastAPI

```python
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from psycopg_pool import AsyncConnectionPool


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = AsyncConnectionPool(settings.db_url, min_size=1, max_size=10)
    await app.state.pool.open()
    yield
    await app.state.pool.close()


app = FastAPI(lifespan=lifespan)


async def get_conn(req: Request):
    async with req.app.state.pool.connection() as conn:
        yield conn


@app.get("/users/{id}")
async def get_user(id: int, conn = Depends(get_conn)):
    async with conn.cursor() as cur:
        await cur.execute("SELECT id, name FROM users WHERE id = %s", (id,))
        return await cur.fetchone()
```

## pgvector

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE docs (id bigserial PRIMARY KEY, embedding vector(768));
CREATE INDEX docs_embedding_idx ON docs USING hnsw (embedding vector_cosine_ops);
```

```python
from pgvector.psycopg import register_vector
import numpy as np, psycopg

with psycopg.connect(url) as conn:
    register_vector(conn)
    with conn.cursor() as cur:
        cur.execute("INSERT INTO docs (embedding) VALUES (%s)", (np.random.rand(768),))
        cur.execute("SELECT id FROM docs ORDER BY embedding <=> %s LIMIT 5",
                    (np.random.rand(768),))
        print(cur.fetchall())
```

## Local dev

```sh
docker run -d --name pg -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:16
psql postgresql://postgres:dev@localhost/postgres
```
