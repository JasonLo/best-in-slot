# Data Model: Bootstrap Discovery Pipeline

**Date**: 2026-05-22 · **Feature**: 001-bootstrap-discovery · **Status**: Phase 1

All entities are Pydantic v2 models in `bis/models.py` (constitution Principle IV). YAML on disk is the source of truth (Principle II); models are I/O boundary types that round-trip through `yaml.safe_load` / `yaml.safe_dump`.

Notation:
- `field: type` — required
- `field: type = default` — optional with default
- `# constraint` — enforced via Pydantic validator or `Annotated[..., Field(...)]`

---

## Mining-phase models

### `RepoRef`
Identifies a single GitHub repository.

```python
class RepoRef(BaseModel):
    owner: str
    name: str
    last_pushed: datetime          # from gh repo metadata; drives 3y window filter
    is_private: bool
    is_org: bool                   # True if owner is an organization
```

### `ToolSignal`
A single observation that a package appears in a repo. Many `ToolSignal`s aggregate into the per-category evidence.

```python
class ToolSignal(BaseModel):
    repo: RepoRef
    package_name: str              # normalised: lowercase, dashes-not-underscores for Python
                                   # scoped names preserved for npm
    manifest_format: str           # e.g., "pyproject.toml", "package.json"
    observed_at: datetime          # = repo.last_pushed (recency proxy for this signal)
```

### `CachedRepoScan`
One file per repo at `.bis/cache/repos/{owner}/{repo}.yaml`. Read path applies the 24h TTL check (FR-015).

```python
class CachedRepoScan(BaseModel):
    repo: RepoRef
    scanned_at: datetime           # used for TTL: now - scanned_at < 24h
    signals: list[ToolSignal]
    scanner_version: str           # bumped when scanner.py output shape changes; cache miss on mismatch
```

### `ProfileSnapshot`
In-memory aggregation of all signals for one bootstrap run. Not persisted directly; consumed by the proposer.

```python
class ProfileSnapshot(BaseModel):
    repos: list[RepoRef]
    signals: list[ToolSignal]
    window_start: datetime         # = now - 3 years
    window_end: datetime           # = now
    skipped_sources: list[SkippedSource] = []
```

### `SkippedSource`
A source (org, private-repo set) that mining could not reach. Surfaced in the run summary (FR-008, SC-004).

```python
class SkippedSource(BaseModel):
    source_id: str                 # e.g., "org:acme-corp", "private:user-repos"
    reason: str                    # "access denied", "rate limit", "scope missing: read:org"
```

---

## Proposal-phase models

### `CategoryProposal`
One draft slot, derived from aggregated signals. Presented to the user during walk-through.

```python
class CategoryProposal(BaseModel):
    category: str                  # e.g., "python-web"
    category_type: Literal["language", "framework", "tooling"]   # drives FR-014 ordering
    proposed_pick: str             # the leading package by evidence_strength
    alternatives: list[str]        # other packages observed in the same category
    evidence_repo_count: int       # how many repos contributed to proposed_pick
    evidence_most_recent: datetime # most recent observation across contributing repos
    evidence_strength: float       # composite score from research.md R-6
    confidence_qualifier: Literal["high", "medium", "low", "conflicting"] | None = None
```

Validator: `confidence_qualifier` is set to `"low"` if `evidence_repo_count < 3`, `"conflicting"` if the top two alternatives' `evidence_strength` are within 10% of each other.

### `SafePayload`  *(FR-013 / R-7)*
The ONLY type permitted as input to LLM-bound functions in `bis/categories.py`. Constructed exclusively by `bis/privacy.py:to_safe_payload()`.

```python
class SafePayloadItem(BaseModel):
    package_name: str
    manifest_format: str           # format name only, never content
    repo_count: int
    most_recent: datetime

class SafePayload(BaseModel):
    items: list[SafePayloadItem]
    # NOTE: any new field here must be reviewed against FR-013.
```

---

## Decision-phase models

### `SlotDecision`
The user's response to one `CategoryProposal`. Emitted by `bis init confirm ...` as JSON. Pick actions (`accept`, `change`) persist into `SlotState.history`; structure actions (`split`, `merge`, `rename`, `drop`, `add`) are translated into a `StructureChange` (see below) and persist into `BootstrapRunState.taxonomy_edits`. `skip`/`defer` persist into `BootstrapRunState` only.

```python
class SlotDecision(BaseModel):
    category: str
    action: Literal["accept", "change", "skip", "defer", "split", "merge", "rename", "drop", "add"]
    chosen_pick: str | None        # required when action in {"accept", "change", "add"}
    into: list[str] | None         # split: optional sub-category names; None = use suggest_split
    merge_with: str | None         # merge: target category to fold into
    new_name: str | None           # rename: new category label
    new_category_type: Literal["language", "framework", "tooling"] | None  # add: type tag for new slot
    was_proposal_unchanged: bool   # True iff action=="accept" or (action=="change" and chosen_pick==proposal.proposed_pick)
    decided_at: datetime
```

Validators (per-action aux requirements):
- `action in {"accept", "change", "add"}` requires `chosen_pick is not None`.
- `action in {"skip", "defer", "split", "merge", "rename", "drop"}` requires `chosen_pick is None`.
- `action == "merge"` requires `merge_with is not None`.
- `action == "rename"` requires `new_name is not None`.
- `action == "add"` requires `new_category_type is not None`.
- `action == "split"` accepts `into = None` (CLI/skill resolves via `suggest_split`) OR `into` with ≥ 2 distinct names.

### `StructureChange`  *(US4 / FR-016, FR-018)*
A single structural edit applied to the proposal set during bootstrap. Append-only audit trail; persisted into `BootstrapRunState.taxonomy_edits` so the next bootstrap run can replay them after fresh mining (FR-018).

```python
class StructureChange(BaseModel):
    kind: Literal["split", "merge", "rename", "drop", "add"]
    category: str                  # the proposal being acted on; for `add`, this is the new slot's name
    into: list[str] | None         # split only — resolved names (auto-suggest or user-supplied)
    merge_with: str | None         # merge only — target category that absorbs this one
    new_name: str | None           # rename only — new category label
    new_pick: str | None           # add only — chosen package for the custom slot
    new_category_type: Literal["language", "framework", "tooling"] | None  # add only
    applied_at: datetime
```

**Invariant**: structure changes preserve evidence (FR-019). `merge_proposals` unions `evidence_repo_count`/alternatives/`evidence_most_recent` over disjoint contributing-repo sets; `apply_rename` is identity-on-evidence; `apply_split` partitions evidence by member-package's heuristic sub-category.

**Trust-boundary note (FR-020)**: `suggest_split` and the merge/rename/drop helpers are **deterministic** — they read only from `CATEGORY_TABLE` and the in-memory proposal set. No LLM call is involved in any structure action. This is enforced by keeping the helpers in `bis/categories.py` outside the `infer_categories_via_llm` path.

**State transition diagram**:

```
                  ┌─────────────┐
                  │  no slot    │
                  └──────┬──────┘
                         │  bootstrap mining
                         ▼
                  ┌─────────────┐
                  │  proposed   │ ◄────────┐
                  └──────┬──────┘          │ next bootstrap
            ┌────────────┼──────────────┐  │ (FR-012, R-9)
            ▼            ▼              ▼  │
       ┌─────────┐  ┌────────┐    ┌─────────┐
       │ accept  │  │ change │    │  defer  │
       └────┬────┘  └────┬───┘    └─────────┘
            │            │
            └──┬─────────┘
               ▼
        ┌─────────────┐
        │  confirmed  │ ──► slot YAML written; optional /deep-dive
        └─────────────┘
                         (skip never persists a slot YAML)
```

---

## Persistence models

### `SlotState`
Persisted as `slots/{category}.yaml`. The state-of-truth for one slot after bootstrap (and after future audit/switch flows from feature 001's predecessor framing).

```python
class SlotState(BaseModel):
    category: str
    category_type: Literal["language", "framework", "tooling"]
    pick: str                      # the currently chosen package
    alternatives: list[str]        # observed alternatives at the time of last decision
    evidence: EvidenceBlock        # snapshot of what made this pick reasonable
    decided_at: datetime
    history: list[HistoryEntry]    # append-only (constitution Skill/CLI Workflow §)

class EvidenceBlock(BaseModel):
    repo_count: int
    most_recent: datetime
    evidence_strength: float
    contributing_repos: list[str]  # "owner/name" identifiers — useful for traceability (SC-003)

class HistoryEntry(BaseModel):
    action: Literal["bootstrap-accept", "bootstrap-change", "bootstrap-skip-(no slot)", "switch"]
    from_pick: str | None          # None on initial bootstrap
    to_pick: str | None            # None on skip
    reason: str                    # non-empty (constitution mandate)
    date: datetime
```

**Invariant**: `history` is append-only. Editing past entries is forbidden outside a documented migration (constitution Skill/CLI Workflow §).

### `BootstrapRunState`
Persisted as `slots/.bootstrap.yaml`. Single file, overwritten each run. Carries resume state across runs (FR-012, SC-007).

```python
class BootstrapRunState(BaseModel):
    run_id: str                    # UUID4
    started_at: datetime
    ended_at: datetime | None      # None if the run is in progress / aborted
    deferred_categories: list[str] # categories the user deferred; resurfaces next run (R-9)
    skipped_sources: list[SkippedSource]
    on_existing_choice: Literal["merge", "replace", "skip"] | None
                                   # populated only when slots already existed at run start
    taxonomy_edits: list[StructureChange] = []
                                   # US4 (FR-018): append-only audit log of structural changes
                                   # applied during this run. Replayed on next bootstrap so
                                   # an aborted-mid-reshape run resumes against the rebuilt
                                   # taxonomy without re-prompting the user for the same edits.
```

**Invariant**: `taxonomy_edits` is append-only (same enforcement shape as `SlotState.history` — `bis/slots.py` exposes `append_taxonomy_edit`, never `edit_taxonomy_edit`).

---

## Relationships

```
            scans                  aggregates into            informs
   gh ──► CachedRepoScan(N) ───► ProfileSnapshot ───► CategoryProposal(N)
                                                              │
                                                              │ user decides
                                                              ▼
                                                       SlotDecision
                                                              │
                                              ┌───────────────┼───────────────┐
                                              │               │               │
                                              ▼               ▼               ▼
                                       persist into     append into     append to
                                       slots/X.yaml    .bootstrap.yaml  .bootstrap.yaml
                                       (SlotState)     deferred_cats    (if "skip" was via batch flag)

   LLM call sites in categories.py:
      argv: SafePayload    ◄── built by privacy.to_safe_payload(ProfileSnapshot)
      (no other type permitted; enforced by function signature + unit test)
```

---

## Validation summary

| Model | Validators / invariants |
|---|---|
| `RepoRef` | `last_pushed` must be tz-aware UTC; `name` must not contain `/`. |
| `ToolSignal` | `package_name` normalised per constitution scanner rules. |
| `CachedRepoScan` | `scanner_version` bumped on output-shape change; mismatched version → cache miss. |
| `CategoryProposal` | `confidence_qualifier` auto-set from `evidence_repo_count` + alternatives spread. |
| `SafePayload` | Fields are an allow-list; adding a field requires reviewing FR-013. |
| `SlotDecision` | `chosen_pick` presence keyed to `action` (validator); structure actions have per-kind aux-field requirements. |
| `StructureChange` | Per-kind aux fields required (e.g., `merge` ⇒ `merge_with`); `applied_at` is tz-aware UTC; append-only via `slots.append_taxonomy_edit`. |
| `SlotState` | `history` is append-only (enforced by `slots.py` API; raw YAML edits will round-trip but break history invariant). |
| `BootstrapRunState` | `on_existing_choice` required iff slots existed at run start; `taxonomy_edits` append-only. |
