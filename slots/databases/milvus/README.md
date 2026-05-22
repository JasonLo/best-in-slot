# milvus

**Slot**: Dedicated vector database for RAG / semantic search at scale (used in `bear`).

## Why milvus

Battle-tested vector DB with HNSW + IVF indexes, hybrid search, partitioning, and a real distributed mode (Milvus 2.x). The Python SDK (`pymilvus`) maps cleanly to Pydantic models.

## When NOT to reach for milvus

Reach for **pgvector on Postgres** ([databases/postgres-psycopg](../postgres-psycopg/)) first if:

- Total vectors < ~10M
- You already have Postgres
- You want transactions across vectors + metadata

Reach for **weaviate** if you prefer a GraphQL API + builtin modules (used in `ask-xDD`, predecessor RAG).

Milvus wins when you're at >10M vectors, need standalone scaling, and operate it as a service.

## Conventions

- Run Milvus standalone in Docker for dev (`milvusdb/milvus:standalone`).
- Use `pymilvus.MilvusClient` (the high-level client), not the low-level grpc API.
- Collections + index defined in code at startup (idempotent `create_collection`).
- Pair with [pydantic](../../python-web/pydantic/) for schema; keep doc IDs as strings.
- Hybrid search: combine vector + scalar filters in one call — don't post-filter in Python.

## Alternatives considered

- **pgvector** — default for small/medium scale.
- **weaviate** — comparable; ask-xDD used it. Ecosystem favours milvus for self-host scale.
- **qdrant** — fine, smaller community.

## Gotchas

- Milvus standalone Docker requires ~2GB RAM and etcd + minio side-cars in `docker-compose`. Don't drop it on a t2.micro.
- IDs must be unique within a collection; auto-id collections lose round-trippable identifiers.
- `MilvusClient.search` returns nested results — flatten in the consumer.
