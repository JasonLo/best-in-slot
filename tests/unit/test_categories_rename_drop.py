"""Unit test: apply_rename and apply_drop are pure data operations (T059).

- rename preserves all evidence; only the `category` field changes
- drop removes the proposal cleanly from a list without affecting siblings
- both round-trip through replay_taxonomy_edits identically (idempotency)
"""

from __future__ import annotations

from datetime import UTC, datetime

from bis.bootstrap import apply_structure_change, replay_taxonomy_edits
from bis.categories import apply_drop, apply_rename
from bis.models import CategoryProposal, StructureChange


def _proposal(category: str, pick: str = "pkg") -> CategoryProposal:
    return CategoryProposal(
        category=category,
        category_type="tooling",
        proposed_pick=pick,
        alternatives=["alt1", "alt2"],
        evidence_repo_count=3,
        evidence_most_recent=datetime(2026, 4, 1, tzinfo=UTC),
        evidence_strength=5.5,
        confidence_qualifier=None,
    )


# --------------------------------------------------------------------------- rename


def test_apply_rename_preserves_evidence():
    proposal = _proposal("databases")
    renamed = apply_rename(proposal, "datastore")
    assert renamed.category == "datastore"
    assert renamed.proposed_pick == proposal.proposed_pick
    assert renamed.alternatives == proposal.alternatives
    assert renamed.evidence_repo_count == proposal.evidence_repo_count
    assert renamed.evidence_most_recent == proposal.evidence_most_recent
    assert renamed.evidence_strength == proposal.evidence_strength
    assert renamed.category_type == proposal.category_type


def test_apply_rename_returns_new_instance():
    """Pure: doesn't mutate input."""

    proposal = _proposal("databases")
    apply_rename(proposal, "datastore")
    assert proposal.category == "databases"


# --------------------------------------------------------------------------- drop


def test_apply_drop_removes_only_target():
    proposals = [_proposal("a"), _proposal("b"), _proposal("c")]
    survived = apply_drop(proposals, "b")
    assert [p.category for p in survived] == ["a", "c"]


def test_apply_drop_missing_target_is_noop():
    proposals = [_proposal("a"), _proposal("b")]
    survived = apply_drop(proposals, "not-present")
    assert [p.category for p in survived] == ["a", "b"]


def test_apply_drop_preserves_remaining_evidence():
    proposals = [_proposal("a"), _proposal("b")]
    survived = apply_drop(proposals, "a")
    assert len(survived) == 1
    assert survived[0].evidence_strength == 5.5  # unchanged


# --------------------------------------------------------------------------- round-trip through replay


def test_rename_drop_round_trip_through_replay():
    proposals = [_proposal("databases"), _proposal("python-terminal"), _proposal("python-web")]
    edits = [
        StructureChange(
            kind="rename",
            category="databases",
            new_name="datastore",
            applied_at=datetime(2026, 5, 1, tzinfo=UTC),
        ),
        StructureChange(
            kind="drop",
            category="python-terminal",
            applied_at=datetime(2026, 5, 2, tzinfo=UTC),
        ),
    ]
    replayed = replay_taxonomy_edits(proposals, edits)
    names = sorted(p.category for p in replayed)
    assert names == ["datastore", "python-web"]


def test_replay_is_deterministic_across_runs():
    """Same input → same output, no hidden state."""

    proposals = [_proposal("a"), _proposal("b")]
    edits = [
        StructureChange(
            kind="rename",
            category="a",
            new_name="alpha",
            applied_at=datetime(2026, 5, 1, tzinfo=UTC),
        ),
    ]
    first = replay_taxonomy_edits(proposals, edits)
    second = replay_taxonomy_edits(proposals, edits)
    assert [p.model_dump() for p in first] == [p.model_dump() for p in second]


def test_apply_structure_change_dispatches_to_rename():
    proposals = [_proposal("databases")]
    change = StructureChange(
        kind="rename",
        category="databases",
        new_name="datastore",
        applied_at=datetime(2026, 5, 1, tzinfo=UTC),
    )
    result = apply_structure_change(change, proposals)
    assert len(result) == 1
    assert result[0].category == "datastore"


def test_apply_structure_change_dispatches_to_drop():
    proposals = [_proposal("a"), _proposal("b")]
    change = StructureChange(
        kind="drop",
        category="a",
        applied_at=datetime(2026, 5, 1, tzinfo=UTC),
    )
    result = apply_structure_change(change, proposals)
    assert [p.category for p in result] == ["b"]
