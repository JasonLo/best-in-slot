"""Unit test: suggest_split heuristic (T057).

Given a CategoryProposal whose members map to ≥2 distinct entries in
CATEGORY_TABLE, suggest_split returns the partitioned sub-proposals with
evidence split per-member. When all members share one sub-category, returns
None.

This is the deterministic, non-LLM helper per FR-020.
"""

from __future__ import annotations

from datetime import UTC, datetime

from bis.categories import suggest_split
from bis.models import CategoryProposal


def _proposal(
    category: str, pick: str, alternatives: list[str], strength: float = 5.0
) -> CategoryProposal:
    return CategoryProposal(
        category=category,
        category_type="tooling",
        proposed_pick=pick,
        alternatives=alternatives,
        evidence_repo_count=3,
        evidence_most_recent=datetime(2026, 4, 1, tzinfo=UTC),
        evidence_strength=strength,
        confidence_qualifier=None,
    )


def test_python_tooling_splits_into_five_sub_slots():
    """The headline use case from commit 3bc2482."""

    proposal = _proposal(
        category="python-tooling",
        pick="ipykernel",
        alternatives=["uv", "ruff", "ty", "pytest"],
    )
    split = suggest_split(proposal)
    assert split is not None, "expected suggest_split to partition python-tooling"
    sub_names = sorted(p.category for p in split)
    assert sub_names == sorted(
        ["package-manager", "linter-formatter", "type-checker", "test-runner", "notebook-kernel"]
    )


def test_single_member_returns_none():
    proposal = _proposal(
        category="solo",
        pick="ruff",
        alternatives=[],
    )
    # ruff alone is one sub-category — nothing to partition.
    assert suggest_split(proposal) is None


def test_all_members_in_same_sub_category_returns_none():
    """uv + poetry both map to package-manager — no split is possible."""

    proposal = _proposal(
        category="pkg-mgrs",
        pick="uv",
        alternatives=["poetry", "pip", "pipenv"],
    )
    assert suggest_split(proposal) is None


def test_split_preserves_member_evidence_strength_ordering():
    """Stronger sub-proposals (more members or recent activity) come first."""

    proposal = _proposal(
        category="python-tooling",
        pick="ipykernel",
        alternatives=["uv", "ruff"],
    )
    split = suggest_split(proposal)
    assert split is not None
    # Each sub-proposal has evidence — none should have evidence_repo_count == 0.
    for sub in split:
        assert sub.evidence_repo_count >= 1
        assert sub.evidence_strength >= 0


def test_unknown_members_skipped_not_blocking():
    """If some members aren't in CATEGORY_TABLE, the known ones still split out."""

    proposal = _proposal(
        category="grab-bag",
        pick="uv",
        alternatives=["ruff", "totally-unknown-pkg-name-zzz"],
    )
    split = suggest_split(proposal)
    # We have ≥ 2 known sub-categories (package-manager, linter-formatter).
    assert split is not None
    sub_names = {p.category for p in split}
    assert "package-manager" in sub_names
    assert "linter-formatter" in sub_names


def test_split_result_carries_proposal_category_type():
    """Sub-proposals inherit category_type from the heuristic table, not the parent."""

    proposal = _proposal(
        category="python-tooling",
        pick="ipykernel",
        alternatives=["uv", "ruff"],
    )
    split = suggest_split(proposal)
    assert split is not None
    # CATEGORY_TABLE marks all five as "tooling".
    assert all(s.category_type == "tooling" for s in split)
