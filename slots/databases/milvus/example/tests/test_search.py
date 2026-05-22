from pathlib import Path

import numpy as np
import pytest

from milvus_example import DIM, ensure_collection, insert_docs, make_client, search


@pytest.fixture
def client(tmp_path: Path):
    db = tmp_path / "milvus.db"
    c = make_client(db)
    ensure_collection(c)
    insert_docs(c, ["doc one", "doc two", "doc three"])
    return c


def test_collection_exists(client) -> None:
    assert client.has_collection("docs")


def test_search_returns_hits(client) -> None:
    rng = np.random.default_rng(seed=1)
    query = rng.random(DIM).tolist()
    results = search(client, query, limit=2)
    assert len(results) == 1
    assert len(results[0]) == 2
    for hit in results[0]:
        assert "entity" in hit
        assert "text" in hit["entity"]
