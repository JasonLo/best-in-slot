# pytest cheatsheet

## Commands

```sh
uv run pytest                  # all tests, verbose-by-default
uv run pytest -q               # quiet
uv run pytest tests/test_x.py::test_y
uv run pytest -k "name_part"
uv run pytest -x               # stop on first failure
uv run pytest --lf             # only last-failed
uv run pytest -m "not slow"
uv run pytest --cov=mypkg      # needs pytest-cov
```

## Snippets

```python
# tests/test_basic.py
import pytest

def test_simple():
    assert 1 + 1 == 2

@pytest.fixture
def sample():
    return {"name": "jason"}

def test_with_fixture(sample):
    assert sample["name"] == "jason"

@pytest.mark.parametrize("n,expected", [(0, 0), (1, 1), (2, 4)])
def test_square(n, expected):
    assert n * n == expected

@pytest.mark.asyncio
async def test_async():
    assert await some_coro() == 42
```

## `pyproject.toml` block

```toml
[dependency-groups]
dev = ["pytest>=8", "pytest-asyncio>=0.24"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
addopts = "-ra"
testpaths = ["tests"]
markers = ["slow: deselect with -m 'not slow'"]
```
