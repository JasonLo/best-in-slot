"""Unit test: `build_structure_overview` returns ordered overview entries (T092).

Pure helper — no I/O, no LLM. Returns one entry per proposal in FR-014 order
(languages → frameworks → tooling, evidence-strength descending within group)
with the optional ``suggest_split_into`` field populated when the heuristic
table can offer a split.
"""

from __future__ import annotations

from datetime import UTC, datetime

from bis.models import CategoryProposal


def _proposal(
    category: str,
    category_type: str,
    pick: str,
    *,
    alternatives: list[str] | None = None,
    repo_count: int = 1,
    strength: float = 1.0,
) -> CategoryProposal:
    return CategoryProposal(
        category=category,
        category_type=category_type,  # type: ignore[arg-type]
        proposed_pick=pick,
        alternatives=alternatives or [],
        evidence_repo_count=repo_count,
        evidence_most_recent=datetime(2026, 5, 1, tzinfo=UTC),
        evidence_strength=strength,
    )


def test_build_structure_overview_returns_one_entry_per_proposal():
    from bis.bootstrap import build_structure_overview

    proposals = [
        _proposal("python", "language", "python"),
        _proposal("python-web", "framework", "fastapi", alternatives=["django"]),
        _proposal("python-tooling", "tooling", "ruff", alternatives=["uv", "pytest"]),
    ]
    overview = build_structure_overview(proposals)
    assert len(overview) == 3


def test_build_structure_overview_preserves_fr014_ordering():
    """Even when input is shuffled, output groups by category_type (language→framework→tooling)."""

    from bis.bootstrap import build_structure_overview

    shuffled = [
        _proposal("python-tooling", "tooling", "ruff", strength=10.0),
        _proposal("python", "language", "python", strength=1.0),
        _proposal("python-web", "framework", "fastapi", strength=5.0),
    ]
    overview = build_structure_overview(shuffled)
    types = [entry.category_type for entry in overview]
    assert types == ["language", "framework", "tooling"], (
        f"FR-014 ordering not preserved: {types!r}"
    )


def test_build_structure_overview_evidence_strength_descending_within_group():
    from bis.bootstrap import build_structure_overview

    proposals = [
        _proposal("a-tool", "tooling", "a", strength=1.0),
        _proposal("b-tool", "tooling", "b", strength=5.0),
        _proposal("c-tool", "tooling", "c", strength=3.0),
    ]
    overview = build_structure_overview(proposals)
    strengths = [entry.evidence_strength for entry in overview]
    assert strengths == sorted(strengths, reverse=True), (
        f"within-group ordering must be evidence-strength descending: {strengths!r}"
    )


def test_build_structure_overview_suggest_split_none_for_single_member():
    """A proposal with no alternatives → suggest_split returns None → field is None."""

    from bis.bootstrap import build_structure_overview

    overview = build_structure_overview([_proposal("python-web", "framework", "fastapi")])
    assert overview[0].suggest_split_into is None


def test_build_structure_overview_suggest_split_populated_for_multi_member():
    """A proposal whose members span ≥2 CATEGORY_TABLE sub-categories surfaces the split."""

    from bis.bootstrap import build_structure_overview

    # python-tooling with uv (package-manager) + ruff (linter) + pytest (test-runner)
    # should trigger suggest_split.
    proposal = _proposal(
        "python-tooling",
        "tooling",
        "ruff",
        alternatives=["uv", "pytest"],
        strength=5.0,
    )
    overview = build_structure_overview([proposal])
    # If the heuristic table maps these to distinct sub-categories, suggest_split_into is populated.
    # The unit test does not pin the exact partition (that's owned by
    # tests/unit/test_categories_split_suggest.py); it only pins that the field is non-None
    # when the underlying suggest_split returns a non-None partition.
    from bis.categories import suggest_split

    expected = suggest_split(proposal)
    if expected is None:
        assert overview[0].suggest_split_into is None
    else:
        assert overview[0].suggest_split_into is not None
        assert len(overview[0].suggest_split_into) >= 2


def test_build_structure_overview_entry_carries_members_list():
    from bis.bootstrap import build_structure_overview

    proposal = _proposal(
        "python-web",
        "framework",
        "fastapi",
        alternatives=["django", "flask"],
    )
    overview = build_structure_overview([proposal])
    members = overview[0].members
    assert members[0] == "fastapi", "proposed_pick must lead the members list"
    assert set(members) == {"fastapi", "django", "flask"}
