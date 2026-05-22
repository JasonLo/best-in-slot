"""Integration test: ``bis init mine`` is mining-only — no walk-through (T072, US5).

US5 splits the bootstrap into two CLI surfaces along the FR-013 trust boundary:

- ``bis init mine --json`` — runs the LLM-touching mining + proposal stage, persists
  the proposal set into ``slots/.bootstrap.yaml`` under ``pending_proposals`` for
  handoff, and exits. Writes no ``slots/{category}.yaml``.
- ``bis init walk`` — reads ``pending_proposals`` and drives the local walk-through.
  Covered by ``test_bootstrap_walk_subcommand.py``.

This test pins the mine-only contract.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
import yaml
from typer.testing import CliRunner

from bis import bootstrap as bootstrap_mod
from bis import cli as cli_mod
from bis.models import ProfileSnapshot, RepoRef, SkippedSource, ToolSignal


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
            ToolSignal(
                repo=repo,
                package_name="ruff",
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


def test_mine_emits_proposals_json_and_persists_pending(patched_pipeline, tmp_slots_root):
    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["init", "mine", "--json"])

    assert result.exit_code == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)

    assert payload["mode"] == "mine"
    assert "run_id" in payload and payload["run_id"]
    assert isinstance(payload["proposals"], list) and len(payload["proposals"]) > 0
    assert payload["pending_proposals_count"] == len(payload["proposals"])

    # Each proposal carries the full shape the walk-through needs.
    for p in payload["proposals"]:
        assert p["category"]
        assert p["category_type"] in ("language", "framework", "tooling")
        assert p["proposed_pick"]
        assert p["evidence_repo_count"] >= 1

    # The proposal set was persisted into .bootstrap.yaml.
    bootstrap_yaml = tmp_slots_root / ".bootstrap.yaml"
    assert bootstrap_yaml.exists()
    persisted = yaml.safe_load(bootstrap_yaml.read_text())
    assert isinstance(persisted.get("pending_proposals"), list)
    assert len(persisted["pending_proposals"]) == len(payload["proposals"])


def test_mine_does_not_write_slot_yamls(patched_pipeline, tmp_slots_root):
    """``bis init mine`` is observation-only — persistence happens at walk time."""

    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["init", "mine", "--json"])
    assert result.exit_code == 0

    slot_files = [p for p in tmp_slots_root.glob("*.yaml") if not p.name.startswith(".")]
    assert slot_files == [], f"expected zero slot YAMLs, found: {[p.name for p in slot_files]}"


def test_mine_includes_skipped_sources_in_payload(patched_pipeline, tmp_slots_root, monkeypatch):
    """Skipped sources flow through unchanged (FR-008 invariant preserved)."""

    profile = _profile().model_copy(
        update={
            "skipped_sources": [
                SkippedSource(source_id="org:acme", reason="access denied"),
            ]
        }
    )
    monkeypatch.setattr(cli_mod, "mine_profile", lambda settings, **kw: profile)

    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["init", "mine", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)

    assert payload["skipped_sources"], "skipped sources must surface in mine payload"
    assert payload["skipped_sources"][0]["source_id"] == "org:acme"


def test_mine_replays_taxonomy_edits_count(patched_pipeline, tmp_slots_root):
    """The mine payload exposes how many taxonomy edits were replayed (FR-018)."""

    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["init", "mine", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)

    # Fresh run — no prior edits.
    assert payload["taxonomy_edits_replayed"] == 0
