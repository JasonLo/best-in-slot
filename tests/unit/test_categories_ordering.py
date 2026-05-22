"""Unit tests for walk-through ordering (T020, FR-014, R-11)."""

from __future__ import annotations

from datetime import datetime, timezone

from bis.categories import order_for_walkthrough
from bis.models import CategoryProposal


def _proposal(category: str, ctype, strength: float) -> CategoryProposal:
    return CategoryProposal(
        category=category,
        category_type=ctype,
        proposed_pick=f"{category}-pick",
        alternatives=[],
        evidence_repo_count=5,
        evidence_most_recent=datetime(2026, 5, 1, tzinfo=timezone.utc),
        evidence_strength=strength,
    )


def test_orders_by_type_group_languages_first_tooling_last():
    props = [
        _proposal("python-tooling", "tooling", 9.0),
        _proposal("python-web", "framework", 5.0),
        _proposal("python", "language", 1.0),
    ]
    ordered = order_for_walkthrough(props)
    assert [p.category_type for p in ordered] == ["language", "framework", "tooling"]


def test_within_group_evidence_strength_descending():
    props = [
        _proposal("a", "framework", 3.0),
        _proposal("b", "framework", 9.0),
        _proposal("c", "framework", 6.0),
    ]
    ordered = order_for_walkthrough(props)
    assert [p.category for p in ordered] == ["b", "c", "a"]


def test_deferred_categories_come_first_in_given_order():
    props = [
        _proposal("python", "language", 1.0),
        _proposal("python-web", "framework", 5.0),
        _proposal("python-tooling", "tooling", 9.0),
    ]
    ordered = order_for_walkthrough(props, deferred=["python-tooling", "python-web"])
    assert [p.category for p in ordered] == ["python-tooling", "python-web", "python"]


def test_ordering_is_deterministic():
    props = [
        _proposal("python-web", "framework", 5.0),
        _proposal("python-data", "framework", 5.0),
        _proposal("python", "language", 1.0),
    ]
    first = order_for_walkthrough(props)
    second = order_for_walkthrough(props)
    assert [p.category for p in first] == [p.category for p in second]
