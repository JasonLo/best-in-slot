"""Integration test: end-to-end bootstrap from zero slots (T014).

Uses an in-memory `ProfileSnapshot` (no subprocess, no network) — the
network layer is mocked via monkeypatch on `bis.cli.mine_profile`. The
test exercises everything from CLI parsing through to slot YAML writes.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

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
        last_pushed=datetime(2026, 4, 1, tzinfo=timezone.utc),
        is_private=False,
        is_org=False,
    )
    repo2 = RepoRef(
        owner="me",
        name="beta",
        last_pushed=datetime(2026, 3, 1, tzinfo=timezone.utc),
        is_private=False,
        is_org=False,
    )
    signals = [
        ToolSignal(repo=repo, package_name="fastapi", manifest_format="pyproject.toml", observed_at=repo.last_pushed),
        ToolSignal(repo=repo, package_name="httpx", manifest_format="pyproject.toml", observed_at=repo.last_pushed),
        ToolSignal(repo=repo2, package_name="fastapi", manifest_format="pyproject.toml", observed_at=repo2.last_pushed),
        ToolSignal(repo=repo2, package_name="ruff", manifest_format="pyproject.toml", observed_at=repo2.last_pushed),
    ]
    return ProfileSnapshot(
        repos=[repo, repo2],
        signals=signals,
        window_start=datetime(2023, 5, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 5, 22, tzinfo=timezone.utc),
    )


@pytest.fixture
def patched_pipeline(monkeypatch, tmp_slots_root, tmp_cache_root):
    profile = _profile()
    monkeypatch.setattr(cli_mod, "mine_profile", lambda settings, **kw: profile)
    monkeypatch.setattr(bootstrap_mod, "check_auth", lambda: None)
    yield


def test_batch_mode_emits_ranked_proposals(patched_pipeline):
    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["bootstrap", "--json", "--batch"])
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    # Walk-through order: languages → frameworks → tooling.
    types = [p["category_type"] for p in payload["proposals"]]
    assert types == sorted(types, key=lambda t: {"language": 0, "framework": 1, "tooling": 2}[t])


def test_batch_mode_proposals_contain_evidence(patched_pipeline):
    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["bootstrap", "--json", "--batch"])
    payload = json.loads(result.stdout)
    for p in payload["proposals"]:
        assert p["evidence_repo_count"] >= 1
        assert "evidence_most_recent" in p
        assert "evidence_strength" in p


def test_confirm_writes_slot_yaml(patched_pipeline, tmp_slots_root):
    runner = CliRunner()
    result = runner.invoke(
        cli_mod.app,
        ["bootstrap", "confirm", "--category", "python-web", "--action", "accept", "--pick", "fastapi", "--json"],
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["mode"] == "confirm"
    assert payload["decision"]["action"] == "accept"
    assert payload["decision"]["chosen_pick"] == "fastapi"
    slot_yaml = tmp_slots_root / "python-web.yaml"
    assert slot_yaml.exists()
    state = yaml.safe_load(slot_yaml.read_text())
    assert state["pick"] == "fastapi"
    assert state["history"][0]["action"] == "bootstrap-accept"


def test_confirm_change_records_history_with_new_pick(patched_pipeline, tmp_slots_root):
    runner = CliRunner()
    result = runner.invoke(
        cli_mod.app,
        ["bootstrap", "confirm", "--category", "python-web", "--action", "change", "--pick", "django", "--json"],
    )
    assert result.exit_code == 0, result.stderr
    state = yaml.safe_load((tmp_slots_root / "python-web.yaml").read_text())
    assert state["pick"] == "django"
    assert state["history"][0]["action"] == "bootstrap-change"
