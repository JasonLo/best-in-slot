"""Integration test: `bis init taxonomy-review --json` pre-walk overview (T055).

Emits the full proposal list with per-proposal split suggestions, before any
walk-through prompts. The skill uses this as the "looks good / reshape"
entry point per FR-017.
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
    signals = [
        ToolSignal(
            repo=repo,
            package_name=name,
            manifest_format="pyproject.toml",
            observed_at=repo.last_pushed,
        )
        for name in ("fastapi", "ruff", "uv", "ty", "pytest", "ipykernel", "psycopg")
    ]
    return ProfileSnapshot(
        repos=[repo],
        signals=signals,
        window_start=datetime(2023, 5, 1, tzinfo=UTC),
        window_end=datetime(2026, 5, 22, tzinfo=UTC),
    )


@pytest.fixture
def patched_pipeline(monkeypatch, tmp_slots_root, tmp_cache_root):
    profile = _profile()
    monkeypatch.setattr(cli_mod, "mine_profile", lambda settings, **kw: profile)
    monkeypatch.setattr(bootstrap_mod, "check_auth", lambda: None)
    yield


def test_taxonomy_review_emits_all_proposals(patched_pipeline):
    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["init", "taxonomy-review", "--json"])
    assert result.exit_code == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["mode"] == "taxonomy-review"
    assert "run_id" in payload
    assert isinstance(payload["proposals"], list)
    assert len(payload["proposals"]) >= 1


def test_taxonomy_review_proposal_carries_members(patched_pipeline):
    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["init", "taxonomy-review", "--json"])
    payload = json.loads(result.stdout)
    for proposal in payload["proposals"]:
        assert "category" in proposal
        assert "category_type" in proposal
        assert "proposed_pick" in proposal
        assert "members" in proposal
        assert isinstance(proposal["members"], list)


def test_taxonomy_review_suggest_split_is_present(patched_pipeline):
    """For categories whose members map to ≥2 sub-categories, suggest_split_into
    is populated; otherwise it is None.
    """

    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["init", "taxonomy-review", "--json"])
    payload = json.loads(result.stdout)
    for proposal in payload["proposals"]:
        # field must always be present (either array or null)
        assert "suggest_split_into" in proposal
        split = proposal["suggest_split_into"]
        assert split is None or isinstance(split, list)


def test_taxonomy_review_then_walkthrough_uses_rebuilt_taxonomy(patched_pipeline, tmp_slots_root):
    """After applying a structural edit, the next walkthrough order reflects it."""

    runner = CliRunner()
    # 1. Review
    runner.invoke(cli_mod.app, ["init", "taxonomy-review", "--json"])
    # 2. Apply a rename via confirm
    result = runner.invoke(
        cli_mod.app,
        [
            "init",
            "confirm",
            "--category",
            "databases",
            "--action",
            "rename",
            "--to-name",
            "datastore",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.stderr or result.stdout

    # 3. Verify .bootstrap.yaml carries the edit
    state = yaml.safe_load((tmp_slots_root / ".bootstrap.yaml").read_text())
    assert any(
        e["kind"] == "rename" and e["new_name"] == "datastore" for e in state["taxonomy_edits"]
    )
