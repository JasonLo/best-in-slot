"""Unit tests for category inference (T021, R-3)."""

from __future__ import annotations

from datetime import UTC, datetime

from bis.categories import (
    CATEGORY_TABLE,
    build_proposals,
    infer_categories_via_llm,
    lookup_category,
)
from bis.models import ProfileSnapshot, RepoRef, SafePayload, ToolSignal


def _now() -> datetime:
    return datetime(2026, 5, 22, tzinfo=UTC)


def _signal(pkg: str, repo_name: str = "demo") -> ToolSignal:
    repo = RepoRef(
        owner="me",
        name=repo_name,
        last_pushed=datetime(2026, 4, 1, tzinfo=UTC),
        is_private=False,
        is_org=False,
    )
    return ToolSignal(
        repo=repo, package_name=pkg, manifest_format="pyproject.toml", observed_at=repo.last_pushed
    )


def test_heuristic_table_hits_known_packages():
    cat, ctype = lookup_category("fastapi")
    assert cat == "python-web"
    assert ctype == "framework"


def test_heuristic_table_misses_unknown_packages():
    assert lookup_category("never-heard-of-this-pkg-xyz123") is None


def test_llm_stub_requires_safepayload():
    import pytest

    with pytest.raises(TypeError):
        infer_categories_via_llm({"items": []})  # type: ignore[arg-type]


def test_llm_stub_returns_empty_for_now():
    # The stub is wired but not implemented; build_proposals just drops unknown packages.
    assert infer_categories_via_llm(SafePayload(items=[])) == {}


def test_build_proposals_picks_strongest_per_category():
    # Two packages in the same category; the one with more repos wins.
    signals = [
        _signal("fastapi", "r1"),
        _signal("fastapi", "r2"),
        _signal("fastapi", "r3"),
        _signal("django", "r4"),
    ]
    profile = ProfileSnapshot(
        repos=[s.repo for s in signals],
        signals=signals,
        window_start=datetime(2023, 5, 1, tzinfo=UTC),
        window_end=_now(),
    )
    proposals = build_proposals(profile, now=_now())
    web = next(p for p in proposals if p.category == "python-web")
    assert web.proposed_pick == "fastapi"
    assert "django" in web.alternatives


def test_build_proposals_skips_unknown_packages():
    signals = [_signal("totally-unknown-package-abc")]
    profile = ProfileSnapshot(
        repos=[signals[0].repo],
        signals=signals,
        window_start=datetime(2023, 5, 1, tzinfo=UTC),
        window_end=_now(),
    )
    assert build_proposals(profile, now=_now()) == []


def test_build_proposals_sets_low_confidence_under_3_repos():
    signals = [_signal("fastapi", "only-one-repo")]
    profile = ProfileSnapshot(
        repos=[signals[0].repo],
        signals=signals,
        window_start=datetime(2023, 5, 1, tzinfo=UTC),
        window_end=_now(),
    )
    [proposal] = build_proposals(profile, now=_now())
    assert proposal.confidence_qualifier == "low"


def test_category_table_has_core_packages():
    """Sanity: seed table covers the existing slots/ content."""

    for pkg in ("fastapi", "pandas", "ruff", "uv", "pytorch", "anthropic", "astro"):
        assert pkg in CATEGORY_TABLE, f"{pkg} missing from heuristic table"
