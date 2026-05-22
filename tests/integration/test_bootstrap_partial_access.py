"""Integration test: partial GitHub access still produces useful output (T017, FR-008, SC-004).

If `gh` errors on one source (e.g., an org we lack access to), the run must:
- record a `SkippedSource` with that source_id
- continue past the error
- still return proposals from sources we *did* reach
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from typer.testing import CliRunner

from bis import bootstrap as bootstrap_mod
from bis import cli as cli_mod
from bis.config import Settings
from bis.models import RepoRef, SkippedSource


@pytest.fixture
def partial_access_doubles(monkeypatch, tmp_slots_root, tmp_cache_root):
    """User has 1 personal repo + 2 orgs; one org returns a 403-style error."""

    user_repo = RepoRef(
        owner="me",
        name="alpha",
        last_pushed=datetime(2026, 4, 1, tzinfo=UTC),
        is_private=False,
        is_org=False,
    )

    def list_user_repos(window, now=None):
        return [user_repo], []

    def list_user_orgs():
        return ["public-org", "secret-org"], []

    def list_org_repos(org, window, now=None):
        if org == "secret-org":
            return [], [
                SkippedSource(
                    source_id=f"org:{org}",
                    reason="HTTP 403: must have admin rights to Organization",
                )
            ]
        return [
            RepoRef(
                owner=org,
                name="zeta",
                last_pushed=datetime(2026, 3, 15, tzinfo=UTC),
                is_private=False,
                is_org=True,
            )
        ], []

    def get_manifest_paths(repo, formats=None):
        return ["pyproject.toml"], []

    def get_manifest_content(repo, path):
        # Both accessible repos use fastapi; secret-org never gets here.
        return '[project]\nname="x"\ndependencies=["fastapi"]\n'

    monkeypatch.setattr(bootstrap_mod, "check_auth", lambda: None)
    monkeypatch.setattr(bootstrap_mod, "list_user_repos", list_user_repos)
    monkeypatch.setattr(bootstrap_mod, "list_user_orgs", list_user_orgs)
    monkeypatch.setattr(bootstrap_mod, "list_org_repos", list_org_repos)
    monkeypatch.setattr(bootstrap_mod, "get_manifest_paths", get_manifest_paths)
    monkeypatch.setattr(bootstrap_mod, "get_manifest_content", get_manifest_content)
    yield


def test_partial_access_completes_and_records_skipped_source(partial_access_doubles):
    profile = bootstrap_mod.mine_profile(Settings())
    skipped_ids = {s.source_id for s in profile.skipped_sources}
    assert "org:secret-org" in skipped_ids
    # We still mined the accessible repos.
    assert any(s.package_name == "fastapi" for s in profile.signals)


def test_partial_access_batch_emits_proposals_plus_skipped(partial_access_doubles):
    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["bootstrap", "--json", "--batch"])
    assert result.exit_code == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    skipped_ids = {s["source_id"] for s in payload["skipped_sources"]}
    assert "org:secret-org" in skipped_ids
    # And proposals came back from the repos we could read.
    assert payload["proposals"], "expected at least one proposal from accessible repos"


def test_partial_access_does_not_emit_auth_error_envelope(partial_access_doubles):
    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["bootstrap", "--json", "--batch"])
    payload = json.loads(result.stdout)
    # gh auth is fine; only one org is gated. The CLI must not conflate this
    # with a global auth failure.
    assert payload["mode"] != "error"
