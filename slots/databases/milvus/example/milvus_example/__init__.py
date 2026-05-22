from pathlib import Path

import numpy as np
from pymilvus import MilvusClient

DIM = 32


def make_client(db_path: str | Path) -> MilvusClient:
    """Return a Milvus-Lite client (zero-install, file-backed)."""
    return MilvusClient(str(db_path))


def ensure_collection(client: MilvusClient, name: str = "docs") -> None:
    if not client.has_collection(name):
        client.create_collection(
            collection_name=name,
            dimension=DIM,
            metric_type="COSINE",
            auto_id=True,
        )


def insert_docs(client: MilvusClient, texts: list[str], name: str = "docs") -> None:
    rng = np.random.default_rng(seed=0)
    rows = [{"vector": rng.random(DIM).tolist(), "text": t} for t in texts]
    client.insert(collection_name=name, data=rows)


def search(client: MilvusClient, query: list[float], limit: int = 3, name: str = "docs"):
    return client.search(
        collection_name=name,
        data=[query],
        limit=limit,
        output_fields=["text"],
    )
