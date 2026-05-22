# milvus cheatsheet

## Connect

```python
from pymilvus import MilvusClient

client = MilvusClient(uri="http://localhost:19530")
# Or Milvus Lite (single-file, no server):
client = MilvusClient("./milvus_demo.db")
```

## Create collection

```python
client.create_collection(
    collection_name="docs",
    dimension=768,
    metric_type="COSINE",          # COSINE | L2 | IP
    auto_id=True,
)
```

## Insert

```python
import numpy as np

vectors = np.random.rand(100, 768).tolist()
client.insert(
    collection_name="docs",
    data=[{"vector": v, "topic": "covid", "text": f"doc {i}"} for i, v in enumerate(vectors)],
)
```

## Search

```python
query = np.random.rand(768).tolist()
hits = client.search(
    collection_name="docs",
    data=[query],
    limit=5,
    output_fields=["text", "topic"],
    filter='topic == "covid"',
)
for h in hits[0]:
    print(h["distance"], h["entity"]["text"])
```

## Docker (standalone) for local dev

```sh
curl -sLO https://github.com/milvus-io/milvus/releases/latest/download/milvus-standalone-docker-compose.yml
docker compose -f milvus-standalone-docker-compose.yml up -d
```

## Lite (zero-install, dev / unit tests)

```python
client = MilvusClient("./milvus_lite.db")
```

Use Lite in tests; Standalone in dev; cluster in prod.
