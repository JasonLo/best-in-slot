"""Pydantic v2 boundary models for the bootstrap discovery pipeline.

All models that cross an I/O boundary (YAML on disk, CLI JSON output, gh subprocess
results, LLM-bound payloads) are defined here. See specs/001-bootstrap-discovery/data-model.md
for the full spec; this file is the implementation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CategoryType = Literal["language", "framework", "tooling"]
DecisionAction = Literal["accept", "change", "skip", "defer"]
HistoryAction = Literal[
    "bootstrap-accept",
    "bootstrap-change",
    "bootstrap-replace",
    "switch",
]
ConfidenceQualifier = Literal["high", "medium", "low", "conflicting"]
ErrorCode = Literal[
    "existing_state_unresolved",
    "no_repos_in_window",
    "gh_auth_missing",
    "scanner_failed",
]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class _Strict(BaseModel):
    """Common config: forbid extras, validate assignment, JSON round-trip safe."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


# --------------------------------------------------------------------------- mining


class RepoRef(_Strict):
    owner: str = Field(min_length=1)
    name: str = Field(min_length=1, pattern=r"^[^/]+$")
    last_pushed: datetime
    is_private: bool
    is_org: bool

    @model_validator(mode="after")
    def _ensure_tz(self) -> RepoRef:
        if self.last_pushed.tzinfo is None:
            raise ValueError("RepoRef.last_pushed must be timezone-aware")
        return self

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.name}"


class ToolSignal(_Strict):
    repo: RepoRef
    package_name: str = Field(min_length=1)
    manifest_format: str = Field(min_length=1)
    observed_at: datetime


class SkippedSource(_Strict):
    source_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class CachedRepoScan(_Strict):
    repo: RepoRef
    scanned_at: datetime
    signals: list[ToolSignal]
    scanner_version: str = Field(min_length=1)


class ProfileSnapshot(_Strict):
    repos: list[RepoRef] = Field(default_factory=list)
    signals: list[ToolSignal] = Field(default_factory=list)
    window_start: datetime
    window_end: datetime
    skipped_sources: list[SkippedSource] = Field(default_factory=list)


# --------------------------------------------------------------------------- proposal


class CategoryProposal(_Strict):
    category: str = Field(min_length=1)
    category_type: CategoryType
    proposed_pick: str = Field(min_length=1)
    alternatives: list[str] = Field(default_factory=list)
    evidence_repo_count: int = Field(ge=1)
    evidence_most_recent: datetime
    evidence_strength: float = Field(ge=0)
    confidence_qualifier: ConfidenceQualifier | None = None


# --------------------------------------------------------------------------- privacy / LLM boundary


class SafePayloadItem(_Strict):
    package_name: str
    manifest_format: str  # format NAME only — never content
    repo_count: int = Field(ge=1)
    most_recent: datetime


class SafePayload(_Strict):
    """The ONLY type permitted as input to any LLM-bound function.

    Constructed exclusively by ``bis.privacy.to_safe_payload``. Adding a field
    here is a privacy decision — review against FR-013 in spec.md.
    """

    items: list[SafePayloadItem] = Field(default_factory=list)


# --------------------------------------------------------------------------- decision


class SlotDecision(_Strict):
    category: str = Field(min_length=1)
    action: DecisionAction
    chosen_pick: str | None = None
    was_proposal_unchanged: bool
    decided_at: datetime = Field(default_factory=_utc_now)

    @model_validator(mode="after")
    def _check_pick(self) -> SlotDecision:
        if self.action in ("accept", "change") and not self.chosen_pick:
            raise ValueError(f"action={self.action!r} requires chosen_pick")
        if self.action in ("skip", "defer") and self.chosen_pick is not None:
            raise ValueError(f"action={self.action!r} forbids chosen_pick")
        return self


# --------------------------------------------------------------------------- persisted slot state


class EvidenceBlock(_Strict):
    repo_count: int = Field(ge=0)
    most_recent: datetime
    evidence_strength: float = Field(ge=0)
    contributing_repos: list[str] = Field(default_factory=list)


class HistoryEntry(_Strict):
    action: HistoryAction
    from_pick: str | None
    to_pick: str | None
    reason: str = Field(min_length=1)
    date: datetime


class SlotState(_Strict):
    category: str = Field(min_length=1)
    category_type: CategoryType
    pick: str = Field(min_length=1)
    alternatives: list[str] = Field(default_factory=list)
    evidence: EvidenceBlock
    decided_at: datetime
    history: list[HistoryEntry] = Field(default_factory=list)


# --------------------------------------------------------------------------- bootstrap-run state


class BootstrapRunState(_Strict):
    run_id: str = Field(min_length=1)
    started_at: datetime
    ended_at: datetime | None = None
    deferred_categories: list[str] = Field(default_factory=list)
    skipped_sources: list[SkippedSource] = Field(default_factory=list)
    on_existing_choice: Literal["merge", "replace", "skip"] | None = None


# --------------------------------------------------------------------------- CLI error envelope


class CliError(_Strict):
    code: ErrorCode
    message: str = Field(min_length=1)
    hint: str | None = None


__all__ = [
    "BootstrapRunState",
    "CachedRepoScan",
    "CategoryProposal",
    "CategoryType",
    "CliError",
    "ConfidenceQualifier",
    "DecisionAction",
    "ErrorCode",
    "EvidenceBlock",
    "HistoryAction",
    "HistoryEntry",
    "ProfileSnapshot",
    "RepoRef",
    "SafePayload",
    "SafePayloadItem",
    "SkippedSource",
    "SlotDecision",
    "SlotState",
    "ToolSignal",
]
