"""Local fast walk-through over an in-memory ``CategoryProposal`` list (US5).

The bootstrap skill `exec`s into this module via ``bis init walk`` after the
LLM-driven ``bis init mine`` step has persisted the proposal set. The walk runs
entirely locally — arrow-key + Enter UX via ``questionary`` for native CLI
speed, no LLM turns in the per-slot loop (FR-022/FR-023).

The ``WalkAdapter`` Protocol is the seam tests use to inject a deterministic
answer stream; ``QuestionaryAdapter`` is the production adapter that talks to
the real TTY; ``ScriptedAdapter`` is the test-only adapter.

``WalkController`` is pure on its inputs and never touches stdout — it iterates
the proposal list, asks the adapter for each decision, optionally fires a
progress callback, and yields one ``SlotDecision`` per proposal in input order.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Literal, Protocol, cast, runtime_checkable

from bis.models import CategoryProposal, DecisionAction, SlotDecision

PickAction = Literal["accept", "change", "skip", "defer"]


@runtime_checkable
class WalkAdapter(Protocol):
    """Source of per-slot answers driving ``WalkController``.

    The controller calls ``select_action`` once per proposal; if the answer is
    ``"change"`` it calls ``select_alternative_or_freeform`` to resolve the new
    pick. Implementations may render UI (``QuestionaryAdapter``) or replay a
    scripted answer stream (``ScriptedAdapter`` in tests).
    """

    def select_action(self, proposal: CategoryProposal) -> PickAction: ...

    def select_alternative_or_freeform(self, proposal: CategoryProposal) -> str: ...


class ScriptedAdapter:
    """Deterministic test adapter — consumes a flat answer stream.

    Each entry corresponds to one proposal in order:
        - ``"accept"`` / ``"skip"`` / ``"defer"`` → action only
        - ``"change:<package>"`` → action=change, pick=<package>

    Raises ``RuntimeError`` if the script is exhausted (too few answers for the
    proposal list) or an entry doesn't parse to a known action.
    """

    def __init__(self, answers: list[str]) -> None:
        self._answers: list[str] = list(answers)
        self._cursor = 0
        self._pending_pick: str | None = None

    def _consume(self) -> str:
        if self._cursor >= len(self._answers):
            raise RuntimeError(
                f"ScriptedAdapter: answer stream exhausted at index {self._cursor}; "
                f"provide more answers"
            )
        ans = self._answers[self._cursor]
        self._cursor += 1
        return ans

    def select_action(self, proposal: CategoryProposal) -> PickAction:
        raw = self._consume()
        if raw.startswith("change:"):
            self._pending_pick = raw.split(":", 1)[1]
            return "change"
        if raw in ("accept", "change", "skip", "defer"):
            self._pending_pick = None
            return cast(PickAction, raw)
        raise ValueError(f"ScriptedAdapter: unknown action {raw!r}")

    def select_alternative_or_freeform(self, proposal: CategoryProposal) -> str:
        if self._pending_pick is None:
            raise RuntimeError(
                f"ScriptedAdapter: no pending pick for change on {proposal.category!r}; "
                f"use 'change:<package>' in the answer stream"
            )
        pick = self._pending_pick
        self._pending_pick = None
        return pick


class QuestionaryAdapter:
    """Real TTY adapter — drives the user through arrow-key + Enter prompts.

    Imports ``questionary`` lazily so the module remains importable in
    environments without a TTY (e.g., test runners that never instantiate it).
    """

    def select_action(self, proposal: CategoryProposal) -> PickAction:
        import questionary

        confidence = f" ({proposal.confidence_qualifier})" if proposal.confidence_qualifier else ""
        alt_summary = (
            f" · alternatives: {', '.join(proposal.alternatives)}" if proposal.alternatives else ""
        )
        message = (
            f"{proposal.category} — proposed pick: {proposal.proposed_pick}"
            f"  [{proposal.evidence_repo_count} repos, "
            f"recent {proposal.evidence_most_recent.date()}{confidence}]"
            f"{alt_summary}"
        )
        choice = questionary.select(
            message,
            choices=[
                {"name": "accept", "value": "accept"},
                {"name": "change pick", "value": "change"},
                {"name": "skip (no slot)", "value": "skip"},
                {"name": "defer (decide later)", "value": "defer"},
            ],
        ).ask()
        if choice is None:  # Ctrl-C / Esc
            raise KeyboardInterrupt
        return choice  # type: ignore[return-value]

    def select_alternative_or_freeform(self, proposal: CategoryProposal) -> str:
        import questionary

        freeform_label = "type a different package name…"
        choices: list[dict[str, str]] = [
            {"name": alt, "value": alt} for alt in proposal.alternatives
        ]
        choices.append({"name": freeform_label, "value": "__freeform__"})
        selected = questionary.select(f"new pick for {proposal.category}?", choices=choices).ask()
        if selected is None:
            raise KeyboardInterrupt
        if selected != "__freeform__":
            return selected
        answer = questionary.text(
            f"package name for {proposal.category}:", default=proposal.proposed_pick
        ).ask()
        if not answer:
            raise KeyboardInterrupt
        return answer


class WalkController:
    """Iterates proposals, asks the adapter, yields one ``SlotDecision`` each.

    Pure on its inputs (no stdout, no slot YAML writes — those are the CLI
    layer's job in ``bis init walk``). The optional ``on_decision`` callback
    fires after each yield so the CLI can print a one-line progress update.
    """

    def __init__(
        self,
        proposals: list[CategoryProposal],
        adapter: WalkAdapter,
        *,
        on_decision: Callable[[int, SlotDecision], None] | None = None,
    ) -> None:
        self.proposals = proposals
        self.adapter = adapter
        self.on_decision = on_decision

    def run(self) -> Iterator[SlotDecision]:
        for idx, proposal in enumerate(self.proposals):
            action = self.adapter.select_action(proposal)
            chosen_pick: str | None
            if action == "accept":
                chosen_pick = proposal.proposed_pick
            elif action == "change":
                chosen_pick = self.adapter.select_alternative_or_freeform(proposal)
            else:
                # skip / defer carry no pick
                chosen_pick = None

            decision_action: DecisionAction = action  # widening from PickAction
            decision = SlotDecision(
                category=proposal.category,
                action=decision_action,
                chosen_pick=chosen_pick,
                was_proposal_unchanged=(
                    action == "accept"
                    or (action == "change" and chosen_pick == proposal.proposed_pick)
                ),
            )
            if self.on_decision is not None:
                self.on_decision(idx, decision)
            yield decision


__all__ = [
    "PickAction",
    "QuestionaryAdapter",
    "ScriptedAdapter",
    "WalkAdapter",
    "WalkController",
]
