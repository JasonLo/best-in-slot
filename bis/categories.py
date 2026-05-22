"""Category inference, evidence-strength scoring, and walk-through ordering.

Two-stage inference (R-3): the heuristic table maps known packages to a
`(category, category_type)` tuple deterministically; unknowns fall through to
an LLM call that receives ONLY a `SafePayload`. The LLM path is implemented as
a stub here — `infer_categories_via_llm` returns `{}`. Wiring it to a real LLM
client is a future feature; the public API is in place so the rest of the
pipeline never needs to change.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime

from bis.models import CategoryProposal, CategoryType, ProfileSnapshot, ToolSignal
from bis.privacy import SafePayload, to_safe_payload  # re-exported for callers

# --------------------------------------------------------------------------- heuristic table
#
# Seeded from the existing slots/ content. Adding rows is the normal way to
# extend coverage; the LLM fallback handles long-tail packages that aren't yet
# in this table.

CATEGORY_TABLE: dict[str, tuple[str, CategoryType]] = {
    # python-web
    "fastapi": ("python-web", "framework"),
    "django": ("python-web", "framework"),
    "flask": ("python-web", "framework"),
    "litestar": ("python-web", "framework"),
    "starlette": ("python-web", "framework"),
    "streamlit": ("python-web", "framework"),
    "gradio": ("python-web", "framework"),
    # python-http-client
    "httpx": ("python-http-client", "tooling"),
    "requests": ("python-http-client", "tooling"),
    "aiohttp": ("python-http-client", "tooling"),
    # python-validation
    "pydantic": ("python-validation", "framework"),
    "pydantic-settings": ("python-config", "tooling"),
    "python-dotenv": ("python-config", "tooling"),
    # python-data
    "pandas": ("python-data", "framework"),
    "polars": ("python-data", "framework"),
    "numpy": ("python-data", "framework"),
    "altair": ("python-data", "tooling"),
    "matplotlib": ("python-data", "tooling"),
    "plotly": ("python-data", "tooling"),
    "jupyter": ("python-data", "tooling"),
    # python-ai
    "pytorch": ("python-ai", "framework"),
    "torch": ("python-ai", "framework"),
    "tensorflow": ("python-ai", "framework"),
    "transformers": ("python-ai", "framework"),
    "anthropic": ("python-ai", "tooling"),
    "openai": ("python-ai", "tooling"),
    "fastmcp": ("python-ai", "tooling"),
    "huggingface-datasets": ("python-data", "tooling"),
    "datasets": ("python-data", "tooling"),
    # python-tooling — split into one category per role, matching the existing
    # slots/python-tooling/ structure (uv / ruff / ty / pytest / ipykernel are
    # each their own slot).
    "uv": ("package-manager", "tooling"),
    "poetry": ("package-manager", "tooling"),
    "pip": ("package-manager", "tooling"),
    "pipenv": ("package-manager", "tooling"),
    "ruff": ("linter-formatter", "tooling"),
    "black": ("linter-formatter", "tooling"),
    "isort": ("linter-formatter", "tooling"),
    "autopep8": ("linter-formatter", "tooling"),
    "ty": ("type-checker", "tooling"),
    "mypy": ("type-checker", "tooling"),
    "pyright": ("type-checker", "tooling"),
    "pytest": ("test-runner", "tooling"),
    "unittest": ("test-runner", "tooling"),
    "nose": ("test-runner", "tooling"),
    "ipykernel": ("notebook-kernel", "tooling"),
    "jupyter-client": ("notebook-kernel", "tooling"),
    # python-terminal
    "typer": ("python-terminal", "framework"),
    "click": ("python-terminal", "framework"),
    "textual": ("python-terminal", "framework"),
    "rich": ("python-terminal", "tooling"),
    # databases
    "psycopg": ("databases", "tooling"),
    "psycopg2": ("databases", "tooling"),
    "sqlalchemy": ("databases", "framework"),
    "sqlmodel": ("databases", "framework"),
    "pymilvus": ("databases", "tooling"),
    "influxdb": ("databases", "tooling"),
    "influxdb-client": ("databases", "tooling"),
    # web-ts (parsed from package.json)
    "astro": ("web-ts", "framework"),
    "hono": ("web-ts", "framework"),
    "bun": ("web-ts", "tooling"),
    "markdown-it": ("web-ts", "tooling"),
    "react": ("web-ts", "framework"),
    "next": ("web-ts", "framework"),
    "vite": ("web-ts", "tooling"),
    # languages (the runtime/language itself when picked from go.mod, Cargo, etc.)
    "go": ("go", "language"),
    "rust": ("rust", "language"),
    "ruby": ("ruby", "language"),
    "python": ("python", "language"),
}


def lookup_category(package_name: str) -> tuple[str, CategoryType] | None:
    """Return the heuristic mapping for a package, or None if unknown."""

    return CATEGORY_TABLE.get(package_name.lower())


# --------------------------------------------------------------------------- LLM fallback


def infer_categories_via_llm(safe: SafePayload) -> dict[str, tuple[str, CategoryType]]:
    """Ask the LLM to classify packages the heuristic table doesn't know.

    Argument type is `SafePayload` — no other type accepted. Current
    implementation is a no-op stub returning `{}`; wiring a real LLM client is a
    follow-up task. The public surface is intentionally stable so adding the
    backend later doesn't ripple through the pipeline.
    """

    if not isinstance(safe, SafePayload):
        raise TypeError(f"infer_categories_via_llm requires SafePayload, got {type(safe).__name__}")
    # Stub: real implementation goes here. See R-3 in research.md.
    return {}


# --------------------------------------------------------------------------- evidence-strength


def evidence_strength(
    repo_count: int, oldest: datetime, most_recent: datetime, now: datetime | None = None
) -> float:
    """Composite score per R-6.

    Higher = stronger evidence. Deterministic given the same inputs.
    """

    if now is None:
        now = datetime.now(UTC)
    months_since_oldest = max(0.0, _months_between(oldest, now))
    months_since_recent = max(0.0, _months_between(most_recent, now))
    breadth = math.log2(1 + months_since_oldest)
    recency_penalty = 1.0 + months_since_recent
    return repo_count * breadth / recency_penalty


def _months_between(earlier: datetime, later: datetime) -> float:
    delta = later - earlier
    return delta.total_seconds() / (60 * 60 * 24 * 30.4375)


# --------------------------------------------------------------------------- proposal construction


def build_proposals(
    profile: ProfileSnapshot, now: datetime | None = None
) -> list[CategoryProposal]:
    """Aggregate the profile's signals into one `CategoryProposal` per category.

    Unknown packages (no heuristic hit, no LLM-inferred category) are dropped —
    they're surfaced in `skipped_sources` upstream rather than fabricating slots.
    """

    if now is None:
        now = datetime.now(UTC)

    # Pre-flight: try to classify all unknowns via the LLM stub.
    unknown_pkgs = {
        sig.package_name for sig in profile.signals if lookup_category(sig.package_name) is None
    }
    llm_map: dict[str, tuple[str, CategoryType]] = {}
    if unknown_pkgs:
        safe = to_safe_payload(profile)
        llm_map = infer_categories_via_llm(safe)

    # Per-category aggregation. Keep type assignments in a separate dict so each
    # value has a single, narrowable type — much friendlier for ty.
    category_types: dict[str, CategoryType] = {}
    picks_per_category: dict[str, dict[str, list[ToolSignal]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for sig in profile.signals:
        match = lookup_category(sig.package_name) or llm_map.get(sig.package_name)
        if match is None:
            continue
        category, category_type = match
        category_types[category] = category_type
        picks_per_category[category][sig.package_name].append(sig)

    proposals: list[CategoryProposal] = []
    for category, picks_map in picks_per_category.items():
        category_type: CategoryType = category_types[category]

        pick_scores: list[tuple[str, float, int, datetime]] = []
        for pkg, sigs in picks_map.items():
            repos = {s.repo.slug for s in sigs}
            most_recent = max(s.observed_at for s in sigs)
            oldest = min(s.observed_at for s in sigs)
            score = evidence_strength(len(repos), oldest, most_recent, now=now)
            pick_scores.append((pkg, score, len(repos), most_recent))

        pick_scores.sort(key=lambda x: x[1], reverse=True)
        winner = pick_scores[0]
        alts = [name for name, *_ in pick_scores[1:]]

        # Confidence qualifier.
        confidence = None
        if winner[2] < 3:
            confidence = "low"
        if (
            confidence is None
            and len(pick_scores) >= 2
            and pick_scores[1][1] > 0
            and abs(winner[1] - pick_scores[1][1]) / max(winner[1], 1e-9) < 0.10
        ):
            confidence = "conflicting"

        proposals.append(
            CategoryProposal(
                category=category,
                category_type=category_type,
                proposed_pick=winner[0],
                alternatives=alts,
                evidence_repo_count=winner[2],
                evidence_most_recent=winner[3],
                evidence_strength=winner[1],
                confidence_qualifier=confidence,
            )
        )
    return proposals


# --------------------------------------------------------------------------- walk-through ordering

_TYPE_ORDER: dict[CategoryType, int] = {"language": 0, "framework": 1, "tooling": 2}


def order_for_walkthrough(
    proposals: Iterable[CategoryProposal], deferred: Iterable[str] = ()
) -> list[CategoryProposal]:
    """Order proposals for the walk-through (FR-014 + R-11).

    Deferred slots come first (FIFO in the given order), then first-time
    proposals grouped languages → frameworks → tooling with evidence-strength
    descending within each group.
    """

    proposals = list(proposals)
    by_category: dict[str, CategoryProposal] = {p.category: p for p in proposals}

    # Deferred-first
    deferred_ordered = [by_category[c] for c in deferred if c in by_category]
    deferred_set = set(deferred)

    first_time = [p for p in proposals if p.category not in deferred_set]
    first_time.sort(key=lambda p: (_TYPE_ORDER[p.category_type], -p.evidence_strength))
    return deferred_ordered + first_time


__all__ = [
    "CATEGORY_TABLE",
    "build_proposals",
    "evidence_strength",
    "infer_categories_via_llm",
    "lookup_category",
    "order_for_walkthrough",
]
