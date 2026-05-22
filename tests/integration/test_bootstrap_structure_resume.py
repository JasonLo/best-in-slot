"""Integration test: resume — taxonomy_edits replay on next run (T056).

Scenario: user applies structural edits (rename + drop), then aborts before
walking through picks. Next bootstrap run does fresh mining; the cached
taxonomy_edits in slots/.bootstrap.yaml are replayed against the new
proposal set so the user isn't asked to redo the structural decisions.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
import yaml
from typer.testing import CliRunner

from bis import bootstrap as bootstrap_mod
from bis import cli as cli_mod
from bis.bootstrap import replay_taxonomy_edits
from bis.models import (
    CategoryProposal,
    ProfileSnapshot,
    RepoRef,
    StructureChange,
    ToolSignal,
)
from bis.slots import read_bootstrap_run_state


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
        for name in ("fastapi", "psycopg", "typer")
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


def test_first_run_persists_taxonomy_edits(patched_pipeline, tmp_slots_root):
    runner = CliRunner()
    runner.invoke(
        cli_mod.app,
        [
            "bootstrap",
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
    runner.invoke(
        cli_mod.app,
        ["bootstrap", "confirm", "--category", "python-terminal", "--action", "drop", "--json"],
    )

    state = yaml.safe_load((tmp_slots_root / ".bootstrap.yaml").read_text())
    edits = state["taxonomy_edits"]
    kinds_and_targets = [(e["kind"], e["category"]) for e in edits]
    assert ("rename", "databases") in kinds_and_targets
    assert ("drop", "python-terminal") in kinds_and_targets


def test_replay_against_fresh_proposals_drops_renames(patched_pipeline):
    """Direct call to replay_taxonomy_edits — verifies the resume semantics."""

    runner = CliRunner()
    runner.invoke(
        cli_mod.app,
        [
            "bootstrap",
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

    # Re-mine produces fresh proposals; replay should rename databases.
    state = read_bootstrap_run_state()
    assert state is not None
    edits = state.taxonomy_edits

    fresh_proposals = [
        CategoryProposal(
            category="databases",
            category_type="tooling",
            proposed_pick="psycopg",
            alternatives=[],
            evidence_repo_count=1,
            evidence_most_recent=datetime(2026, 4, 1, tzinfo=UTC),
            evidence_strength=2.0,
        ),
        CategoryProposal(
            category="python-web",
            category_type="framework",
            proposed_pick="fastapi",
            alternatives=[],
            evidence_repo_count=1,
            evidence_most_recent=datetime(2026, 4, 1, tzinfo=UTC),
            evidence_strength=2.0,
        ),
    ]
    replayed = replay_taxonomy_edits(fresh_proposals, edits)
    names = sorted(p.category for p in replayed)
    assert "datastore" in names
    assert "databases" not in names


def test_replay_is_idempotent(patched_pipeline):
    """Running replay twice yields the same proposal set."""

    edits = [
        StructureChange(
            kind="rename",
            category="databases",
            new_name="datastore",
            applied_at=datetime(2026, 5, 1, tzinfo=UTC),
        ),
    ]
    proposals = [
        CategoryProposal(
            category="databases",
            category_type="tooling",
            proposed_pick="psycopg",
            alternatives=[],
            evidence_repo_count=1,
            evidence_most_recent=datetime(2026, 4, 1, tzinfo=UTC),
            evidence_strength=2.0,
        ),
    ]
    once = replay_taxonomy_edits(proposals, edits)
    twice = replay_taxonomy_edits(once, edits)
    # rename of a non-existent "databases" in the second pass is a no-op
    assert [p.category for p in once] == [p.category for p in twice]


def test_replay_skips_edits_with_missing_targets(patched_pipeline):
    """If a cached edit references a category no longer in the proposal set
    (e.g., the user's repo activity changed), the edit is silently skipped
    rather than crashing the resume.
    """

    edits = [
        StructureChange(
            kind="rename",
            category="gone-from-history",
            new_name="renamed",
            applied_at=datetime(2026, 5, 1, tzinfo=UTC),
        ),
    ]
    proposals = [
        CategoryProposal(
            category="still-here",
            category_type="tooling",
            proposed_pick="pkg",
            alternatives=[],
            evidence_repo_count=1,
            evidence_most_recent=datetime(2026, 4, 1, tzinfo=UTC),
            evidence_strength=2.0,
        ),
    ]
    replayed = replay_taxonomy_edits(proposals, edits)
    assert [p.category for p in replayed] == ["still-here"]
