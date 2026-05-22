# pytest

**Slot**: Python test runner.

## Why pytest

The de-facto standard. Function-style tests, powerful fixtures, async support via `pytest-asyncio`, and an enormous plugin ecosystem when you actually need it.

## Conventions

- Tests live in `tests/` at repo root; files named `test_*.py`; functions named `test_*`.
- Use plain `assert` (pytest rewrites them for diff output).
- Async tests: add `pytest-asyncio` and set `asyncio_mode = "auto"` so you can drop `@pytest.mark.asyncio`.
- Fixtures in a top-level `conftest.py` shared across the suite.
- One test asserts one thing.
- Don't import the package under test by path-fiddling — install it editable (`uv sync` does this).

## Alternatives considered

- **unittest** — stdlib, fine for tiny projects; verbose for anything real.
- **nose2** — abandoned for most purposes.

## Gotchas

- Fixture scope (`function`, `module`, `session`) matters for speed when tests share expensive state.
- Mark slow tests with `@pytest.mark.slow` and skip in default runs (`-m "not slow"`).
- `tmp_path` and `monkeypatch` are usually all the mocking you need before reaching for `unittest.mock`.
