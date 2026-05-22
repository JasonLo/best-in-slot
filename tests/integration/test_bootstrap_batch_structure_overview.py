"""Integration test: `bis init --json --batch` emits `proposed_structure_overview` (T091).

Batch mode is non-interactive — the confirm prompt MUST NOT fire — but the JSON
payload gains a `proposed_structure_overview` field alongside the existing
`proposals` field so consumers can render structure decisions without a second
CLI call.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
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
            ToolSignal(
                repo=repo,
                package_name="ruff",
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


def test_batch_emits_proposed_structure_overview(patched_pipeline):
    runner = CliRunner()
    # No stdin — if any prompt fires, this fails.
    result = runner.invoke(cli_mod.app, ["init", "--json", "--batch"])
    assert result.exit_code == 0, result.stderr or result.stdout

    payload = json.loads(result.stdout)
    assert payload["mode"] == "batch"
    assert "proposals" in payload, "existing field must still be present"
    assert "proposed_structure_overview" in payload, (
        "US6 (FR-025) — batch output must include proposed_structure_overview"
    )

    overview = payload["proposed_structure_overview"]
    assert isinstance(overview, list)
    # One entry per proposal, with the documented shape.
    assert len(overview) == len(payload["proposals"])
    for entry in overview:
        for required_field in ("category", "category_type", "proposed_pick", "members"):
            assert required_field in entry, f"overview entry missing {required_field!r}: {entry!r}"
        # suggest_split_into is nullable; just assert the key exists.
        assert "suggest_split_into" in entry


def test_batch_overview_has_no_interactive_prompt(patched_pipeline):
    """No 'looks good' / 'reshape' string in batch stdout (CliRunner has no stdin)."""

    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["init", "--json", "--batch"])
    assert result.exit_code == 0
    assert "looks good" not in result.stdout.lower()
    assert "reshape" not in result.stdout.lower()


def test_batch_overview_ordering_matches_proposals(patched_pipeline):
    """The overview entries must align positionally with `proposals` (FR-014 order)."""

    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["init", "--json", "--batch"])
    payload = json.loads(result.stdout)
    proposal_cats = [p["category"] for p in payload["proposals"]]
    overview_cats = [o["category"] for o in payload["proposed_structure_overview"]]
    assert proposal_cats == overview_cats, (
        "overview categories must match proposals positionally (same FR-014 ordering)"
    )
