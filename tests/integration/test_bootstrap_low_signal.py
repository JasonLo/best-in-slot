"""Integration test: low-signal edge cases (T047, spec § Edge Cases)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from typer.testing import CliRunner

from bis import bootstrap as bootstrap_mod
from bis import cli as cli_mod
from bis.models import ProfileSnapshot, RepoRef, ToolSignal


def _profile(signals: list[ToolSignal]) -> ProfileSnapshot:
    return ProfileSnapshot(
        repos=list({s.repo.slug: s.repo for s in signals}.values()),
        signals=signals,
        window_start=datetime(2023, 5, 1, tzinfo=UTC),
        window_end=datetime(2026, 5, 22, tzinfo=UTC),
    )


@pytest.fixture
def runner():
    return CliRunner()


def test_no_repos_in_window_emits_error_envelope(monkeypatch, tmp_slots_root, tmp_cache_root, runner):
    """A user with no repos in the 3y window gets a clean error, not a crash."""

    monkeypatch.setattr(cli_mod, "mine_profile", lambda settings, **kw: _profile(signals=[]))
    monkeypatch.setattr(bootstrap_mod, "check_auth", lambda: None)

    result = runner.invoke(cli_mod.app, ["bootstrap", "--json", "--batch"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["mode"] == "error"
    assert payload["error"]["code"] == "no_repos_in_window"


def test_single_repo_proposal_carries_low_confidence(monkeypatch, tmp_slots_root, tmp_cache_root, runner):
    """A category supported by < 3 repos surfaces with confidence_qualifier=low."""

    repo = RepoRef(
        owner="me",
        name="solo",
        last_pushed=datetime(2026, 4, 1, tzinfo=UTC),
        is_private=False,
        is_org=False,
    )
    sig = ToolSignal(
        repo=repo,
        package_name="fastapi",
        manifest_format="pyproject.toml",
        observed_at=repo.last_pushed,
    )
    monkeypatch.setattr(cli_mod, "mine_profile", lambda settings, **kw: _profile([sig]))
    monkeypatch.setattr(bootstrap_mod, "check_auth", lambda: None)

    result = runner.invoke(cli_mod.app, ["bootstrap", "--json", "--batch"])
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    [p] = payload["proposals"]
    assert p["confidence_qualifier"] == "low"


def test_gh_auth_missing_emits_error_envelope(monkeypatch, tmp_slots_root, tmp_cache_root, runner):
    from bis.models import SkippedSource

    profile = ProfileSnapshot(
        repos=[],
        signals=[],
        window_start=datetime(2023, 5, 1, tzinfo=UTC),
        window_end=datetime(2026, 5, 22, tzinfo=UTC),
        skipped_sources=[SkippedSource(source_id="auth", reason="gh auth status failed")],
    )
    monkeypatch.setattr(cli_mod, "mine_profile", lambda settings, **kw: profile)
    monkeypatch.setattr(bootstrap_mod, "check_auth", lambda: None)

    result = runner.invoke(cli_mod.app, ["bootstrap", "--json", "--batch"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "gh_auth_missing"
    assert "gh auth login" in payload["error"]["hint"]
