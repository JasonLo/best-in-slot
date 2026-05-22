"""Latency regression for the local walk-through (T083, US5 / SC-011).

Drives ``WalkController`` through the deterministic ``ScriptedAdapter`` against a
20-proposal fixture and asserts the system-side per-decision latency stays
under budget:

- SC-011 budget: p95 < 200ms.
- This test enforces a tighter p95 < 50ms because the deterministic adapter
  does no I/O — anything slower means a regression in ``WalkController`` or
  Pydantic validation, not in the TTY layer.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

from bis.models import CategoryProposal
from bis.walk import ScriptedAdapter, WalkController


def _proposal(category: str, pick: str) -> CategoryProposal:
    return CategoryProposal(
        category=category,
        category_type="framework",
        proposed_pick=pick,
        alternatives=[],
        evidence_repo_count=3,
        evidence_most_recent=datetime(2026, 4, 1, tzinfo=UTC),
        evidence_strength=1.0,
        confidence_qualifier="high",
    )


def test_walk_latency_p95_under_budget_for_20_proposals() -> None:
    n = 20
    proposals = [_proposal(f"cat-{i}", f"pick-{i}") for i in range(n)]
    adapter = ScriptedAdapter(["accept"] * n)
    controller = WalkController(proposals, adapter)

    iterator = controller.run()
    latencies: list[float] = []
    while True:
        start = time.perf_counter()
        try:
            next(iterator)
        except StopIteration:
            break
        latencies.append(time.perf_counter() - start)

    assert len(latencies) == n
    latencies.sort()
    p95 = latencies[int(0.95 * n) - 1]

    # Reported in the failure message so CI logs show how close we are to budget.
    assert p95 < 0.05, (
        f"per-decision p95 latency {p95 * 1000:.2f}ms exceeds 50ms "
        f"(SC-011 user-facing budget is 200ms — tighter here because the "
        f"deterministic adapter does no I/O)"
    )

    # Total system-side wall-clock for the whole walk under 4s (SC-012 backstop).
    assert sum(latencies) < 4.0, (
        f"total system-side wall-clock {sum(latencies) * 1000:.0f}ms over budget"
    )
