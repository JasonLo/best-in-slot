"""Integration test: existing-state handling (T018, FR-007, SC-005)."""

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
    return ProfileSnapshot(
        repos=[repo],
        signals=[
            ToolSignal(
                repo=repo,
                package_name="fastapi",
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


def _seed_existing_slot(slots_dir, category="python-web", pick="django"):
    (slots_dir / f"{category}.yaml").write_text(
        yaml.safe_dump(
            {
                "category": category,
                "category_type": "framework",
                "pick": pick,
                "alternatives": [],
                "evidence": {
                    "repo_count": 1,
                    "most_recent": "2025-12-01T00:00:00+00:00",
                    "evidence_strength": 1.0,
                    "contributing_repos": [],
                },
                "decided_at": "2025-12-01T00:00:00+00:00",
                "history": [],
            }
        )
    )


def test_batch_without_on_existing_errors_loudly(patched_pipeline, tmp_slots_root):
    _seed_existing_slot(tmp_slots_root)
    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["bootstrap", "--json", "--batch"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["mode"] == "error"
    assert payload["error"]["code"] == "existing_state_unresolved"
    # And the existing slot is untouched.
    state = yaml.safe_load((tmp_slots_root / "python-web.yaml").read_text())
    assert state["pick"] == "django"


def test_batch_with_skip_preserves_existing(patched_pipeline, tmp_slots_root):
    _seed_existing_slot(tmp_slots_root)
    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["bootstrap", "--json", "--batch", "--on-existing=skip"])
    assert result.exit_code == 0, result.stderr
    state = yaml.safe_load((tmp_slots_root / "python-web.yaml").read_text())
    assert state["pick"] == "django"  # unchanged


def test_replace_records_bootstrap_replace_history(patched_pipeline, tmp_slots_root):
    _seed_existing_slot(tmp_slots_root, pick="django")
    runner = CliRunner()
    result = runner.invoke(
        cli_mod.app,
        [
            "bootstrap",
            "confirm",
            "--category",
            "python-web",
            "--action",
            "accept",
            "--pick",
            "fastapi",
            "--json",
            "--on-existing=replace",
        ],
    )
    assert result.exit_code == 0, result.stderr
    state = yaml.safe_load((tmp_slots_root / "python-web.yaml").read_text())
    actions = [h["action"] for h in state["history"]]
    assert "bootstrap-replace" in actions
    assert state["pick"] == "fastapi"
