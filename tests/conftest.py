"""Shared pytest fixtures for the bootstrap discovery test suite."""

from __future__ import annotations

import json
import os
import stat
from datetime import UTC, datetime, timezone
from pathlib import Path

import pytest

# --------------------------------------------------------------------------- paths


@pytest.fixture
def tmp_cache_root(tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the bis cache root at `.bis/cache/repos` into a tmp dir.

    The cache module reads `BIS_CACHE_ROOT` if set; tests rely on that hook.
    """

    cache_root = Path(tmp_path) / "bis-cache" / "repos"  # type: ignore[arg-type]
    cache_root.mkdir(parents=True)
    monkeypatch.setenv("BIS_CACHE_ROOT", str(cache_root))
    return cache_root


@pytest.fixture
def tmp_slots_root(tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> Path:
    slots_root = Path(tmp_path) / "slots"  # type: ignore[arg-type]
    slots_root.mkdir(parents=True)
    monkeypatch.setenv("BIS_SLOTS_ROOT", str(slots_root))
    return slots_root


# --------------------------------------------------------------------------- gh stub


@pytest.fixture
def gh_stub(tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Register a fake `gh` executable on PATH that reads canned JSON.

    The stub looks up `$BIS_GH_FIXTURE_DIR` for files matching the requested
    endpoint. Tests populate that dir with `*.json` files keyed by URL fragment.
    """

    fixture_dir = Path(tmp_path) / "gh-fixtures"  # type: ignore[arg-type]
    fixture_dir.mkdir()

    stub_dir = Path(tmp_path) / "stub-bin"  # type: ignore[arg-type]
    stub_dir.mkdir()
    stub = stub_dir / "gh"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        'fixture_dir="${BIS_GH_FIXTURE_DIR}"\n'
        'if [[ "$1" == "auth" && "$2" == "status" ]]; then\n'
        '  exit "${BIS_GH_AUTH_EXIT:-0}"\n'
        "fi\n"
        'if [[ "$1" == "api" ]]; then\n'
        '  endpoint="$2"\n'
        "  # collapse the endpoint into a filename: replace / and ? with _\n"
        '  safe=$(echo "$endpoint" | tr "/?&=" "____")\n'
        '  fixture="${fixture_dir}/${safe}.json"\n'
        '  if [[ -f "$fixture" ]]; then\n'
        '    cat "$fixture"\n'
        "    exit 0\n"
        "  fi\n"
        '  echo "{\\"message\\": \\"no fixture for ${endpoint}\\"}" >&2\n'
        "  exit 1\n"
        "fi\n"
        'echo "gh stub: unsupported invocation: $*" >&2\n'
        "exit 2\n"
    )
    st = stub.stat()
    stub.chmod(st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    monkeypatch.setenv("BIS_GH_FIXTURE_DIR", str(fixture_dir))
    monkeypatch.setenv("PATH", f"{stub_dir}{os.pathsep}{os.environ['PATH']}")
    return fixture_dir


# --------------------------------------------------------------------------- time


@pytest.fixture
def frozen_now(monkeypatch: pytest.MonkeyPatch) -> datetime:
    """Freeze the wall clock for deterministic recency math.

    Use `monkeypatch.setattr` to patch any `datetime.now` callers the code
    under test imports. The returned value is the frozen instant.
    """

    fake_now = datetime(2026, 5, 22, 12, 0, 0, tzinfo=UTC)

    class _FakeDateTime(datetime):
        @classmethod
        def now(cls, tz: timezone | None = None) -> datetime:  # type: ignore[override]
            return fake_now if tz is None else fake_now.astimezone(tz)

    monkeypatch.setattr("bis.cache.datetime", _FakeDateTime, raising=False)
    return fake_now


# --------------------------------------------------------------------------- helpers


def write_gh_fixture(fixture_dir: Path, endpoint: str, payload: object) -> Path:
    """Helper for tests: write a JSON fixture under the endpoint's stub key.

    Endpoint string is the same as the gh stub script's collapse rule:
    `/` `?` `&` `=` → `_`.
    """

    safe = endpoint.translate(str.maketrans("/?&=", "____"))
    out = fixture_dir / f"{safe}.json"
    out.write_text(json.dumps(payload))
    return out
