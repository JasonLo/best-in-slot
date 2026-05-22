"""Bootstrap pipeline orchestration.

End-to-end glue between mining (`github` + `scanner` + `cache`), proposing
(`categories`), and persisting (`slots`). Keeps the CLI in `bis.cli` thin.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from bis.cache import get_cached_scan, put_cached_scan
from bis.categories import build_proposals, order_for_walkthrough
from bis.config import Settings
from bis.github import (
    GhUnavailable,
    check_auth,
    get_manifest_content,
    get_manifest_paths,
    list_org_repos,
    list_user_orgs,
    list_user_repos,
)
from bis.models import (
    BootstrapRunState,
    CachedRepoScan,
    CategoryProposal,
    EvidenceBlock,
    HistoryEntry,
    ProfileSnapshot,
    RepoRef,
    SkippedSource,
    SlotDecision,
    SlotState,
    ToolSignal,
)
from bis.privacy import SCANNER_VERSION
from bis.scanner import scan_manifest
from bis.slots import (
    list_existing_slot_categories,
    read_bootstrap_run_state,
    read_slot_state,
    write_bootstrap_run_state,
    write_slot_state,
)

# --------------------------------------------------------------------------- existing state


def detect_existing_state() -> list[str]:
    """Return the categories that already have a slot YAML on disk."""

    return list_existing_slot_categories()


# --------------------------------------------------------------------------- mining


def mine_profile(settings: Settings, *, now: datetime | None = None) -> ProfileSnapshot:
    """Scan repos in the trailing window and aggregate per-tool signals.

    Uses the per-repo cache (~24h TTL) so retries within the window are cheap.
    Errors degrade into `SkippedSource` entries.
    """

    now = now or datetime.now(UTC)
    window = settings.mining_window
    skipped: list[SkippedSource] = []

    try:
        check_auth()
    except GhUnavailable as exc:
        # Propagate as a special skipped source; the CLI layer turns this into an error envelope.
        skipped.append(SkippedSource(source_id="auth", reason=str(exc)))
        return ProfileSnapshot(
            repos=[],
            signals=[],
            window_start=now - window,
            window_end=now,
            skipped_sources=skipped,
        )

    user_repos, user_skipped = list_user_repos(window, now=now)
    skipped.extend(user_skipped)

    orgs, org_list_skipped = list_user_orgs()
    skipped.extend(org_list_skipped)

    org_repos: list[RepoRef] = []
    for org in orgs:
        repos, s = list_org_repos(org, window, now=now)
        skipped.extend(s)
        org_repos.extend(repos)

    repos = _dedupe_repos(user_repos + org_repos)
    signals: list[ToolSignal] = []

    for repo in repos:
        cached = get_cached_scan(repo, ttl=settings.cache_ttl)
        if cached is not None:
            signals.extend(cached.signals)
            continue
        # Cache miss → fetch + scan.
        paths, fetch_skipped = get_manifest_paths(repo)
        skipped.extend(fetch_skipped)
        new_signals: list[ToolSignal] = []
        for path in paths:
            try:
                content = get_manifest_content(repo, path)
                names = scan_manifest(path, content)
            except Exception as exc:  # noqa: BLE001 — degrade per-file errors
                skipped.append(SkippedSource(source_id=f"repo:{repo.slug}:{path}", reason=str(exc)))
                continue
            for name in names:
                new_signals.append(
                    ToolSignal(
                        repo=repo,
                        package_name=name,
                        manifest_format=Path(path).name,
                        observed_at=repo.last_pushed,
                    )
                )
        # Persist cache even when empty — avoids re-fetching unchanged repos.
        put_cached_scan(
            CachedRepoScan(
                repo=repo,
                scanned_at=now,
                signals=new_signals,
                scanner_version=SCANNER_VERSION,
            )
        )
        signals.extend(new_signals)

    return ProfileSnapshot(
        repos=repos,
        signals=signals,
        window_start=now - window,
        window_end=now,
        skipped_sources=skipped,
    )


def _dedupe_repos(repos: Iterable[RepoRef]) -> list[RepoRef]:
    seen: set[str] = set()
    out: list[RepoRef] = []
    for r in repos:
        if r.slug in seen:
            continue
        seen.add(r.slug)
        out.append(r)
    return out


# --------------------------------------------------------------------------- proposals + ordering


def proposals_for_walkthrough(
    profile: ProfileSnapshot, deferred: Iterable[str] = (), *, now: datetime | None = None
) -> list[CategoryProposal]:
    raw = build_proposals(profile, now=now)
    return order_for_walkthrough(raw, deferred=deferred)


def walkthrough_iter(
    proposals: Iterable[CategoryProposal],
) -> Iterator[CategoryProposal]:
    """Yield proposals one at a time (placeholder for any future iterator state)."""

    yield from proposals


# --------------------------------------------------------------------------- decision application


def apply_decision(
    decision: SlotDecision,
    proposal: CategoryProposal,
    *,
    on_existing: str = "merge",
) -> Path | None:
    """Persist the user's decision; return the written slot YAML path, or None for skip/defer.

    `on_existing` governs how an existing `SlotState` is treated:
      - "merge" / default: append a history entry on top of existing state
      - "replace": overwrite (a `bootstrap-replace` history entry records the swap)
    """

    if decision.action in ("skip", "defer"):
        return None

    pick = decision.chosen_pick
    if pick is None:  # defensive; SlotDecision validator already enforces this
        raise ValueError(f"action={decision.action!r} requires chosen_pick")

    existing = read_slot_state(decision.category)
    history: list[HistoryEntry] = []
    if existing is not None:
        if on_existing == "replace":
            history = [
                *existing.history,
                HistoryEntry(
                    action="bootstrap-replace",
                    from_pick=existing.pick,
                    to_pick=pick,
                    reason="bootstrap re-run with --on-existing=replace",
                    date=decision.decided_at,
                ),
            ]
        else:
            history = [*existing.history]
    history.append(
        HistoryEntry(
            action="bootstrap-accept" if decision.action == "accept" else "bootstrap-change",
            from_pick=existing.pick if existing else None,
            to_pick=pick,
            reason=(
                "bootstrap: accepted proposed pick"
                if decision.action == "accept"
                else f"bootstrap: changed from proposed {proposal.proposed_pick!r}"
            ),
            date=decision.decided_at,
        )
    )

    state = SlotState(
        category=decision.category,
        category_type=proposal.category_type,
        pick=pick,
        alternatives=proposal.alternatives,
        evidence=EvidenceBlock(
            repo_count=proposal.evidence_repo_count,
            most_recent=proposal.evidence_most_recent,
            evidence_strength=proposal.evidence_strength,
            contributing_repos=[],  # populated by a future pass that tracks signals→repos
        ),
        decided_at=decision.decided_at,
        history=history,
    )
    return write_slot_state(state)


# --------------------------------------------------------------------------- run state


def start_run_state(
    *, on_existing_choice: Literal["merge", "replace", "skip"] | None = None
) -> BootstrapRunState:
    prior = read_bootstrap_run_state()
    deferred = list(prior.deferred_categories) if prior else []
    state = BootstrapRunState(
        run_id=str(uuid.uuid4()),
        started_at=datetime.now(UTC),
        ended_at=None,
        deferred_categories=deferred,
        skipped_sources=[],
        on_existing_choice=on_existing_choice,
    )
    write_bootstrap_run_state(state)
    return state


def record_deferral(state: BootstrapRunState, category: str) -> BootstrapRunState:
    if category not in state.deferred_categories:
        state = state.model_copy(
            update={"deferred_categories": [*state.deferred_categories, category]}
        )
        write_bootstrap_run_state(state)
    return state


def clear_deferral(state: BootstrapRunState, category: str) -> BootstrapRunState:
    if category in state.deferred_categories:
        new = [c for c in state.deferred_categories if c != category]
        state = state.model_copy(update={"deferred_categories": new})
        write_bootstrap_run_state(state)
    return state


def end_run_state(state: BootstrapRunState, skipped: list[SkippedSource]) -> BootstrapRunState:
    state = state.model_copy(update={"ended_at": datetime.now(UTC), "skipped_sources": skipped})
    write_bootstrap_run_state(state)
    return state


__all__ = [
    "apply_decision",
    "clear_deferral",
    "detect_existing_state",
    "end_run_state",
    "mine_profile",
    "proposals_for_walkthrough",
    "record_deferral",
    "start_run_state",
    "walkthrough_iter",
]
