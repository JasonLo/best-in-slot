"""Integration test: deferred slots persist and resurface on the next run (T015).

Covers FR-012, SC-007, R-9, R-11. The flow:
1. A previous run recorded `deferred_categories` in `slots/.bootstrap.yaml`.
2. A fresh `--json --batch` invocation must:
   - report those categories in `deferred_categories_resurfaced`
   - place them at the top of the `proposals` list (R-11 ordering rule)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
import yaml
from typer.testing import CliRunner

from bis import bootstrap as bootstrap_mod
from bis import cli as cli_mod
from bis.models import ProfileSnapshot, RepoRef, ToolSignal


def _profile() -> ProfileSnapshot:
    repo = RepoRef(
        owner="me",
        name="alpha",
        last_pushed=datetime(2026, 4, 1, tzinfo=UTC),
        is_private=False,
        is_org=False,
    )
    # fastapi → python-web (framework), pytest → test-runner (tooling).
    # Without deferral, ordering puts the framework first; if test-runner is
    # deferred, it must jump to the front.
    return ProfileSnapshot(
        repos=[repo],
        signals=[
            ToolSignal(
                repo=repo,
                package_name="fastapi",
                manifest_format="pyproject.toml",
                observed_at=repo.last_pushed,
            ),
            ToolSignal(
                repo=repo,
                package_name="pytest",
                manifest_format="pyproject.toml",
                observed_at=repo.last_pushed,
            ),
        ],
        window_start=datetime(2023, 5, 1, tzinfo=UTC),
        window_end=datetime(2026, 5, 22, tzinfo=UTC),
    )


@pytest.fixture
def patched_pipeline(monkeypatch, tmp_slots_root, tmp_cache_root):
    profile = _profile()
    monkeypatch.setattr(cli_mod, "mine_profile", lambda settings, **kw: profile)
    monkeypatch.setattr(bootstrap_mod, "check_auth", lambda: None)
    yield


def _seed_deferred(slots_root, categories: list[str]) -> None:
    """Write a `.bootstrap.yaml` mimicking the tail of a prior run."""

    (slots_root / ".bootstrap.yaml").write_text(
        yaml.safe_dump(
            {
                "run_id": "prior-run",
                "started_at": "2026-05-01T00:00:00+00:00",
                "ended_at": "2026-05-01T00:30:00+00:00",
                "deferred_categories": categories,
                "skipped_sources": [],
                "on_existing_choice": None,
            }
        )
    )


def test_deferred_categories_resurface_at_top(patched_pipeline, tmp_slots_root):
    _seed_deferred(tmp_slots_root, ["test-runner"])
    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["bootstrap", "--json", "--batch"])
    assert result.exit_code == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert "test-runner" in payload["deferred_categories_resurfaced"]
    # Walk-through ordering: deferred-first, then language → framework → tooling.
    categories_in_order = [p["category"] for p in payload["proposals"]]
    assert categories_in_order[0] == "test-runner"


def test_deferral_state_round_trips_through_run_state(patched_pipeline, tmp_slots_root):
    """After a fresh run finishes, the deferred list is preserved on disk."""

    _seed_deferred(tmp_slots_root, ["test-runner"])
    runner = CliRunner()
    runner.invoke(cli_mod.app, ["bootstrap", "--json", "--batch"])
    after = yaml.safe_load((tmp_slots_root / ".bootstrap.yaml").read_text())
    # The new run inherits the prior deferred list (it has not been resolved).
    assert "test-runner" in after["deferred_categories"]


def test_no_deferral_falls_through_to_default_ordering(patched_pipeline):
    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["bootstrap", "--json", "--batch"])
    payload = json.loads(result.stdout)
    assert payload["deferred_categories_resurfaced"] == []
    types = [p["category_type"] for p in payload["proposals"]]
    assert types == sorted(types, key=lambda t: {"language": 0, "framework": 1, "tooling": 2}[t])
