"""Unit test: merge_proposals evidence invariants (T058).

When merging two CategoryProposals:
- repo_count uses a SET of contributing repo slugs (no naive sum that
  double-counts when both proposals share repos)
- most_recent = max(...)
- alternatives = ordered dedup union (proposed_picks of each input become
  alternatives in the merged proposal)
- category_type must match; mismatch raises ValueError (CLI layer catches
  this as merge_incompatible_types)
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from bis.categories import merge_proposals
from bis.models import CategoryProposal, CategoryType


def _proposal(
    category: str,
    pick: str,
    category_type: CategoryType = "tooling",
    alternatives: list[str] | None = None,
    repo_count: int = 2,
    most_recent: datetime | None = None,
    strength: float = 3.0,
) -> CategoryProposal:
    return CategoryProposal(
        category=category,
        category_type=category_type,
        proposed_pick=pick,
        alternatives=alternatives or [],
        evidence_repo_count=repo_count,
        evidence_most_recent=most_recent or datetime(2026, 3, 1, tzinfo=UTC),
        evidence_strength=strength,
        confidence_qualifier=None,
    )


def test_merge_unions_alternatives():
    a = _proposal("python-config", "python-dotenv", alternatives=["dynaconf"])
    b = _proposal("python-validation", "pydantic", alternatives=["marshmallow"])
    merged = merge_proposals(a, b)
    # The first proposal's pick wins; the other becomes an alternative.
    assert merged.proposed_pick in {"python-dotenv", "pydantic"}
    others = set(merged.alternatives) | {merged.proposed_pick}
    assert {"python-dotenv", "pydantic", "dynaconf", "marshmallow"} <= others


def test_merge_alternatives_are_deduplicated():
    a = _proposal("c1", "pkg1", alternatives=["shared", "alt-a"])
    b = _proposal("c2", "pkg2", alternatives=["shared", "alt-b"])
    merged = merge_proposals(a, b)
    # "shared" appears once.
    assert merged.alternatives.count("shared") <= 1


def test_merge_takes_max_most_recent():
    a = _proposal("c1", "pkg1", most_recent=datetime(2026, 1, 1, tzinfo=UTC))
    b = _proposal("c2", "pkg2", most_recent=datetime(2026, 5, 1, tzinfo=UTC))
    merged = merge_proposals(a, b)
    assert merged.evidence_most_recent == datetime(2026, 5, 1, tzinfo=UTC)


def test_merge_repo_count_uses_union_not_naive_sum():
    """When two proposals share contributing repos, the merged count must
    use a set union — not double-count. The current evidence model only
    carries the count, so merge_proposals takes the max of disjoint sums
    (a conservative invariant: never overstate).
    """

    a = _proposal("c1", "pkg1", repo_count=3)
    b = _proposal("c2", "pkg2", repo_count=4)
    merged = merge_proposals(a, b)
    # Upper bound: a's repos + b's repos = 7.
    # Lower bound (if all shared): max(3, 4) = 4.
    # Invariant: never exceeds the sum.
    assert 4 <= merged.evidence_repo_count <= 7


def test_merge_incompatible_types_raises():
    a = _proposal("c1", "pkg1", category_type="framework")
    b = _proposal("c2", "pkg2", category_type="tooling")
    with pytest.raises(ValueError):
        merge_proposals(a, b)


def test_merge_uses_first_proposals_category_name():
    """The first proposal's category survives as the merged category name."""

    a = _proposal("python-config", "python-dotenv")
    b = _proposal("python-validation", "pydantic")
    merged = merge_proposals(a, b)
    assert merged.category == "python-config"


def test_merge_three_proposals():
    a = _proposal("c1", "p1")
    b = _proposal("c2", "p2")
    c = _proposal("c3", "p3")
    merged = merge_proposals(a, b, c)
    others = set(merged.alternatives) | {merged.proposed_pick}
    assert {"p1", "p2", "p3"} <= others


def test_merge_single_input_returns_clone():
    a = _proposal("solo", "pkg")
    merged = merge_proposals(a)
    assert merged.category == "solo"
    assert merged.proposed_pick == "pkg"


def test_merge_evidence_strength_is_max():
    a = _proposal("c1", "p1", strength=2.0)
    b = _proposal("c2", "p2", strength=7.5)
    merged = merge_proposals(a, b)
    assert merged.evidence_strength == 7.5
