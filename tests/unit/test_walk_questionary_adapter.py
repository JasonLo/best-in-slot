"""Unit tests for ``bis/walk.py`` — the fast questionary-driven walk-through (T075, US5).

Covers:
- ``WalkAdapter`` Protocol — a deterministic ``ScriptedAdapter`` test double satisfies it.
- ``WalkController`` — given proposals and an adapter, yields one ``SlotDecision`` per
  proposal, in input order.
- Latency budget — system-side per-decision time (with the deterministic adapter
  that does not touch the TTY) must be < 50 ms (cf. SC-011 budget of 200 ms p95).
- Error surface — the adapter raises when the answer stream is exhausted or contains
  an unknown action.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

import pytest

from bis.models import CategoryProposal


def _proposal(category: str, pick: str, alternatives: list[str] | None = None) -> CategoryProposal:
    return CategoryProposal(
        category=category,
        category_type="framework",
        proposed_pick=pick,
        alternatives=alternatives or [],
        evidence_repo_count=3,
        evidence_most_recent=datetime(2026, 4, 1, tzinfo=UTC),
        evidence_strength=1.0,
        confidence_qualifier="high",
    )


def test_scripted_adapter_emits_one_decision_per_proposal() -> None:
    from bis.walk import ScriptedAdapter, WalkController

    proposals = [
        _proposal("python-web", "fastapi", ["django"]),
        _proposal("python-data", "pandas"),
        _proposal("linter", "ruff"),
        _proposal("type-checker", "mypy"),
    ]
    adapter = ScriptedAdapter(["accept", "change:polars", "skip", "defer"])

    decisions = list(WalkController(proposals, adapter).run())

    assert [d.action for d in decisions] == ["accept", "change", "skip", "defer"]
    assert decisions[0].chosen_pick == "fastapi"
    assert decisions[1].chosen_pick == "polars"  # change-to alternative
    assert decisions[2].chosen_pick is None  # skip clears pick
    assert decisions[3].chosen_pick is None  # defer clears pick
    assert [d.category for d in decisions] == [p.category for p in proposals]


def test_scripted_adapter_was_proposal_unchanged_flag() -> None:
    from bis.walk import ScriptedAdapter, WalkController

    proposals = [
        _proposal("a", "fastapi"),  # accept ⇒ unchanged
        _proposal("b", "pandas"),  # change to same name ⇒ unchanged
        _proposal("c", "ruff"),  # change to different name ⇒ changed
    ]
    adapter = ScriptedAdapter(["accept", "change:pandas", "change:black"])

    decisions = list(WalkController(proposals, adapter).run())

    assert decisions[0].was_proposal_unchanged is True
    assert decisions[1].was_proposal_unchanged is True
    assert decisions[2].was_proposal_unchanged is False


def test_scripted_adapter_raises_when_answers_exhausted() -> None:
    from bis.walk import ScriptedAdapter, WalkController

    proposals = [_proposal("a", "x"), _proposal("b", "y")]
    adapter = ScriptedAdapter(["accept"])  # only one answer for two proposals

    with pytest.raises((IndexError, RuntimeError, StopIteration)):
        list(WalkController(proposals, adapter).run())


def test_scripted_adapter_rejects_unknown_action() -> None:
    from bis.walk import ScriptedAdapter, WalkController

    proposals = [_proposal("a", "x")]
    adapter = ScriptedAdapter(["nuke"])  # not a valid action

    with pytest.raises((ValueError, RuntimeError)):
        list(WalkController(proposals, adapter).run())


def test_per_decision_system_latency_under_budget() -> None:
    """SC-011 budget is 200ms p95; the deterministic path should be < 50ms each."""

    from bis.walk import ScriptedAdapter, WalkController

    n = 20
    proposals = [_proposal(f"cat-{i}", f"pick-{i}") for i in range(n)]
    adapter = ScriptedAdapter(["accept"] * n)

    controller = WalkController(proposals, adapter)
    latencies: list[float] = []
    iterator = controller.run()
    while True:
        start = time.perf_counter()
        try:
            next(iterator)
        except StopIteration:
            break
        latencies.append(time.perf_counter() - start)

    assert len(latencies) == n
    # Sort ascending; p95 is index ceil(0.95 * n) - 1 = 18 for n=20.
    latencies.sort()
    p95 = latencies[int(0.95 * n) - 1]
    assert p95 < 0.05, f"p95 per-decision latency {p95 * 1000:.1f}ms exceeds 50ms budget"


def test_progress_callback_fires_after_each_decision() -> None:
    from bis.walk import ScriptedAdapter, WalkController

    proposals = [_proposal("a", "x"), _proposal("b", "y")]
    adapter = ScriptedAdapter(["accept", "skip"])
    seen: list[tuple[int, str]] = []
    controller = WalkController(
        proposals, adapter, on_decision=lambda idx, d: seen.append((idx, d.action))
    )

    list(controller.run())

    assert seen == [(0, "accept"), (1, "skip")]
