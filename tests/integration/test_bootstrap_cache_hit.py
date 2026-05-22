"""Integration test: warm-cache run skips the network entirely (T016, SC-009).

The constitutional contract is "re-runs within TTL must not re-fetch", not a
wall-clock target — wall-clock tests are flaky. We assert the stronger claim
by making `get_manifest_paths`/`get_manifest_content` raise on the second run;
if the cache works, those never get called.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from bis import bootstrap as bootstrap_mod
from bis.config import Settings
from bis.models import RepoRef, SkippedSource


def _repo() -> RepoRef:
    return RepoRef(
        owner="me",
        name="alpha",
        last_pushed=datetime(2026, 4, 1, tzinfo=UTC),
        is_private=False,
        is_org=False,
    )


@pytest.fixture
def github_double(monkeypatch, tmp_slots_root, tmp_cache_root):
    """Replace the bis.github surface used by mine_profile with controllable doubles."""

    state = {"manifest_calls": 0, "content_calls": 0}

    def list_user_repos(window, now=None):
        return [_repo()], []

    def list_user_orgs():
        return [], []

    def list_org_repos(org, window, now=None):
        return [], []

    def get_manifest_paths(repo, formats=None):
        state["manifest_calls"] += 1
        return ["pyproject.toml"], []

    def get_manifest_content(repo, path):
        state["content_calls"] += 1
        return '[project]\nname="x"\ndependencies=["fastapi"]\n'

    monkeypatch.setattr(bootstrap_mod, "check_auth", lambda: None)
    monkeypatch.setattr(bootstrap_mod, "list_user_repos", list_user_repos)
    monkeypatch.setattr(bootstrap_mod, "list_user_orgs", list_user_orgs)
    monkeypatch.setattr(bootstrap_mod, "list_org_repos", list_org_repos)
    monkeypatch.setattr(bootstrap_mod, "get_manifest_paths", get_manifest_paths)
    monkeypatch.setattr(bootstrap_mod, "get_manifest_content", get_manifest_content)
    return state


def test_cold_run_then_warm_run_skips_manifest_fetches(github_double):
    settings = Settings()
    profile1 = bootstrap_mod.mine_profile(settings)
    assert any(s.package_name == "fastapi" for s in profile1.signals)
    cold_manifest_calls = github_double["manifest_calls"]
    cold_content_calls = github_double["content_calls"]
    assert cold_manifest_calls == 1
    assert cold_content_calls == 1

    profile2 = bootstrap_mod.mine_profile(settings)
    # Cache hit ⇒ no additional manifest or content fetches.
    assert github_double["manifest_calls"] == cold_manifest_calls
    assert github_double["content_calls"] == cold_content_calls
    # Signals come from cache and round-trip identically.
    assert [s.package_name for s in profile2.signals] == [s.package_name for s in profile1.signals]


def test_warm_run_does_not_record_synthetic_auth_skip(github_double):
    settings = Settings()
    bootstrap_mod.mine_profile(settings)
    profile2 = bootstrap_mod.mine_profile(settings)
    assert not any(
        isinstance(s, SkippedSource) and s.source_id == "auth" for s in profile2.skipped_sources
    )
