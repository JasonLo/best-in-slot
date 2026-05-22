# Research: Bootstrap Discovery Pipeline

**Date**: 2026-05-22 · **Feature**: 001-bootstrap-discovery · **Status**: Phase 0 complete

This document resolves the technical decisions the spec deliberately deferred and the planning-phase open items flagged in `checklists/requirements.md`. Every decision is justified against the constitution and the five clarifications recorded in `spec.md § Clarifications`.

---

## R-1. Per-repo mining cache: format & location

**Decision**: One YAML file per repo at `.bis/cache/repos/{owner}/{repo}.yaml`. Each file holds a `CachedRepoScan` record (see data-model.md) with a `scanned_at` ISO-8601 timestamp. Read path checks `now - scanned_at < 24h`; otherwise re-scans and overwrites. Cache root `.bis/` is gitignored.

**Rationale**: One-file-per-repo gives free per-entry invalidation, lets reviewers/users grep + diff individual scans, and avoids the locking pain of a single growing file. YAML satisfies constitution Principle II (no databases). The 24h TTL matches FR-015 and answers Q5's clarification ("per-repo cache with short TTL").

**Alternatives considered**:
- SQLite — rejected by constitution Principle II.
- Single `cache.yaml` — rejected: requires a file lock for concurrent scans; partial invalidation is awkward; manual inspection ("why didn't this repo refresh?") devolves into YAML grep.
- `~/.cache/bis/` (XDG base dir) — appealing but cross-project state leaks across multiple `bis` checkouts; keep cache project-local.

---

## R-2. Manifest parser coverage for v1

**Decision**: Ship parsers for these manifest formats in `bis/scanner.py`:

| Format | Source ecosystem | Extraction |
|---|---|---|
| `pyproject.toml` | Python | `[project].dependencies`, `[project.optional-dependencies]`, `[tool.poetry.dependencies]`, `[tool.pixi.dependencies]` |
| `requirements.txt` / `requirements-*.txt` | Python (legacy) | Line-by-line, strip versions/extras |
| `package.json` | Node / TypeScript | `dependencies`, `devDependencies`, `peerDependencies` |
| `go.mod` | Go | `require` block |
| `Cargo.toml` | Rust | `[dependencies]`, `[dev-dependencies]` |
| `Gemfile` | Ruby | `gem 'name'` lines |

**Rationale**: Covers ≥95% of repos in typical full-stack inventories without committing to obscure formats up front. Each parser returns `dict[str, list[str]]` of normalised package names (constitution mandate: lowercase, dashes-not-underscores for Python, scoped names preserved for npm).

**Alternatives considered**:
- "All manifests" (Gradle, Maven, Pipfile, poetry.lock, pixi.lock, Brewfile, etc.) — rejected for v1; adds long-tail surface that only a fraction of users need. Future parsers go into the same module without API changes.
- Static-analysis import-graph parsing (read source for `import X`) — rejected: violates FR-013 (raw source content would have to leave the manifest layer).

---

## R-3. Category inference: heuristic-first, LLM-on-unknowns

**Decision**: A two-stage inference in `bis/categories.py`:

1. **Heuristic table** maps known packages to a `(category, category_type)` tuple — e.g., `fastapi → (python-web, framework)`, `numpy → (python-data, framework)`, `ruff → (python-tooling, tooling)`. Lives in a module-level dict, versioned with code. Covers the user's existing slots and the long tail of well-known packages.
2. **LLM fallback** for packages that don't hit the table: send a `SafePayload` (names, frequencies, recency — see R-7) to the LLM asking "suggest a category label and one of language|framework|tooling for each name."

Decisions land in the heuristic table over time, so cost trends to zero as the table grows.

**Rationale**: Constitution Principle I ("Python does data, Claude does judgment") puts category inference on the edge — deterministic core, LLM only where the table is silent. Keeps the bootstrap reproducible for known packages, lets it stay useful for novel ones. Q2's clarification (only names + counts + recency cross the boundary) is satisfied by the same `SafePayload`.

**Alternatives considered**:
- Pure-heuristic — rejected: silently drops packages not in the table, which is exactly what the user wants flagged.
- Pure-LLM — rejected: non-deterministic, expensive on every run, and the cache (R-1) doesn't help because category assignment is a per-package question, not a per-repo one.
- Embeddings + nearest-neighbor against a curated reference set — appealing but adds a vector dependency for a problem the heuristic table handles for ≥80% of inputs.

---

## R-4. Category-type taxonomy (language / framework / tooling)

**Decision**: `category_type` is one of three literal values, set at category-inference time and persisted in `slots/{category}.yaml`:

- **language**: the category is a programming language ecosystem itself (e.g., `python`, `rust`, `typescript`). Slot pick names the *runtime/interpreter or core toolchain* the user prefers (e.g., `python` slot pick = `python 3.14 via uv`).
- **framework**: a substantive library that shapes how code is structured (e.g., `python-web` → `fastapi`, `python-data` → `pandas`, `python-ai` → `pytorch`).
- **tooling**: developer-experience or infrastructure tools the user reaches for repeatedly (e.g., `python-lint` → `ruff`, `python-pkg` → `uv`, `container-runtime` → `apptainer`).

**Rationale**: Q4's clarification mandates this 3-tier grouping for walk-through ordering (languages first, tooling last). Three buckets are coarse enough that every category fits without arguments, fine enough to produce a meaningful walk-through order ("start with the foundation, end with the polish"). Mapping lives in the heuristic table from R-3.

**Alternatives considered**:
- Finer taxonomy (e.g., `runtime`, `web-framework`, `db-driver`, `cli-tool`, `linter`, …) — rejected: every additional bucket invites bikeshedding without changing the walk-through behaviour.
- User-defined — rejected for v1: forces every user into a taxonomy decision before they've seen their proposals. Future iteration could allow overrides.

---

## R-5. Walk-through transport: CLI ↔ skill ↔ user

**Decision**: Three CLI surfaces, picked by flag:

1. **`bis bootstrap --interactive`** (default) — synchronous TTY prompts. Used when running directly in a terminal.
2. **`bis bootstrap --json --batch`** — emits the full proposal set as a single JSON document; no prompts. Used by the skill to fetch the structured proposal, then drive the conversation in chat.
3. **`bis bootstrap confirm --category X --action accept|change|skip|defer [--pick name]`** — applies one decision; emits the resulting `SlotDecision` as JSON. Used by both surfaces to apply decisions.

The bootstrap skill in `skills/bis-bootstrap/SKILL.md` works by: (a) calling `--json --batch` once to load proposals, (b) walking the user through them in the conversation, (c) calling `bis bootstrap confirm ...` per accepted/changed/skipped/deferred slot, (d) offering `/deep-dive` per confirmed slot.

**Rationale**: Constitution Principle III ("Skills wrap the CLI") — the CLI carries the structured contract; the skill is a thin conversational driver. Other agents (CI, scripts) can use `--json --batch` + `confirm` without ever invoking the skill.

**Alternatives considered**:
- CLI emits NDJSON of `WalkthroughEvent`s and reads stdin for responses (stream + duplex) — appealing for skill use but harder to test and overcomplicates the terminal case. Deferred to a future "skill drives long-running CLI" pattern if one emerges.
- Skill calls into Python directly via a wrapper — rejected: violates Principle III; couples skill to internals.

---

## R-6. Evidence-strength scoring (for walk-through tiebreak)

**Decision**: Composite score per proposal, used only for ordering within a category-type group (FR-014):

```
evidence_strength = repo_count * log2(1 + months_since_oldest_signal) / (1 + months_since_most_recent_signal)
```

Higher = stronger evidence. Deterministic given the same input data. Lives in `bis/categories.py`.

**Rationale**: The formula rewards both breadth (more repos) and recency (a tool used 6 months ago beats one last touched 2 years ago) while not punishing a long history. SC-002 (≥70% accept rate) requires that the strongest-evidence proposals genuinely *are* the user's preferred picks, so ordering directly affects measurability.

**Alternatives considered**:
- Raw `repo_count` — rejected: a tool used in 10 abandoned 2022 repos would outrank a tool used in 4 active 2025 repos.
- LLM-judged ordering — rejected: non-determinism breaks SC-002 measurement and violates Principle I.
- Recency-only — rejected: a one-off `cowsay` use last week would outrank everything else.

---

## R-7. Trust-boundary scrubbing (FR-013)

**Decision**: A `SafePayload` Pydantic model in `bis/models.py` is the *only* type permitted as an argument to LLM-bound functions. It contains:

```python
class SafePayload(BaseModel):
    items: list[SafePayloadItem]

class SafePayloadItem(BaseModel):
    package_name: str
    manifest_format: str    # e.g., "pyproject.toml" — format name only, not content
    repo_count: int
    most_recent: datetime
```

Constructed only via `bis/privacy.py:to_safe_payload(profile_snapshot)`. Unit test `test_privacy_scrubber.py` asserts that the JSON serialisation of any `SafePayload` contains *no* substring that appears in raw manifest bodies, repo names beyond the package layer, or README content.

**Rationale**: Q2's clarification + FR-013 + SC-008 require an enforceable invariant, not a discipline. Forcing the type at the function signature converts a runtime hazard into a type-check + grep-able pattern. Reviewers can `grep -r 'to_safe_payload\|SafePayload' bis/` to verify every LLM call goes through the scrubber.

**Alternatives considered**:
- Pre-call assertion in each LLM call site — rejected: too easy to forget; failures are silent leaks.
- A wrapper LLM client that strips on the way out — rejected: stripping requires knowing what's safe, which is the same logic; better to never construct the unsafe payload at all.

---

## R-8. Existing-state detection (FR-007)

**Decision**: At the start of every `bis bootstrap` run, `bis/bootstrap.py:detect_existing_state()` checks for any non-hidden `*.yaml` under `slots/`. If found, the run pauses and requires:
- In `--interactive` mode: a prompt asking `merge / replace / skip`.
- In `--json --batch` mode: the request must include `--on-existing={merge|replace|skip}` or it returns an error JSON document.

**Rationale**: FR-007 + SC-005 require an explicit user choice 100% of the time. Failing-loudly in `--batch` mode prevents the skill (or any script) from accidentally overwriting prior state with a default.

**Alternatives considered**:
- Default to `merge` — rejected: silent merge can still surprise the user (e.g., resurrected old picks).
- Treat presence of `slots/.bootstrap.yaml` as the signal — rejected: a user could have curated `slots/*.yaml` by hand without ever running bootstrap.

---

## R-9. Resume of deferred slots (FR-012, SC-007)

**Decision**: `slots/.bootstrap.yaml` carries a `deferred_categories: list[str]` field. At the start of the next `bis bootstrap` walk-through, those categories are pulled to the *top* of the queue (regardless of category-type grouping) so the user sees their unfinished business first. Once decided, the category is removed from `deferred_categories`. The file also tracks `skipped_sources` (FR-008) and `run_id` for telemetry.

**Rationale**: Q3's clarification + SC-007 — deferred slots resurface on next run, no cooldown. Putting them at the top (overriding the language → framework → tooling grouping for these specific slots) signals "you owe these answers" rather than burying them in the normal sequence.

**Alternatives considered**:
- Re-mix deferred slots into their natural position in the order — rejected: the user already saw them once; surfacing them prominently is the point.
- Resurface only when the user explicitly asks — rejected by Q3's clarification (option A: automatic resurface).

---

## R-10. Deep-dive chaining strategy (FR-005, User Story 2)

**Decision**: Per-slot offer with deferred batch fallback. After each `confirm accept|change`, the skill asks "Run /deep-dive on this slot now? [Y/n/all-later/skip-all]". `all-later` queues the slot for a single batch invocation at the end of the walk-through; `skip-all` disables the prompt for the rest of the run.

The CLI side just persists the `SlotState`; the skill handles the prompt and invokes `/deep-dive` (out-of-process slash command). The CLI never invokes `/deep-dive` directly.

**Rationale**: Per-slot is the natural rhythm but a power user who knows they want deep-dives on everything shouldn't be prompted 15 times. Defer-to-batch is the escape hatch. Constitution Principle III is preserved: CLI doesn't know about skills.

**Alternatives considered**:
- Always per-slot — rejected: annoying for users who batch-process.
- Always batch at end — rejected: the per-slot offer is a natural quality gate (user can change their mind about a slot before the dive starts).
- CLI invokes deep-dive — rejected: violates Principle III (CLI shelling to a skill inverts the dependency).

---

## R-11. Walk-through ordering deferred slots vs first-run slots

**Decision** (refinement of R-9): The walk-through order in a run with both deferred and first-time proposals is:

1. **Deferred slots first**, in the order they were originally deferred (FIFO).
2. Then **first-time proposals**, grouped languages → frameworks → tooling, evidence-strength descending within each group (FR-014).

**Rationale**: Resolves an ambiguity left in FR-014: it specifies the ordering for first-run proposals but doesn't say where deferred slots go. Putting deferred first matches R-9's "unfinished business" framing.

---

## R-12. Open scope decisions deferred from the spec checklist

The Phase 0 research closes both items the requirements checklist flagged:

- **"Where deferred-state and per-repo cache live"** → Sidecar `slots/.bootstrap.yaml` for run state (R-9), `.bis/cache/repos/{owner}/{repo}.yaml` for cache (R-1). Slot YAMLs stay focused on confirmed-pick state.
- **"Whether the merge/replace/skip choice is offered globally, per-slot, or both"** → Globally per run (R-8). Per-slot would multiply the prompts without giving the user new information (they already chose per-slot accept/change/skip/defer for proposals).

---

## Constitution re-check after Phase 0

| Principle | Status | Notes |
|---|---|---|
| I — Python does data, Claude does judgment | PASS | Heuristic table is data; LLM only invoked with SafePayload on unknowns. |
| II — YAML is source of truth | PASS | All persistence is YAML files. |
| III — Skills wrap CLI | PASS | Skill calls `bis bootstrap --json --batch` + `bis bootstrap confirm`; CLI does not know about skills. |
| IV — Modern toolchain | PASS | uv, Typer, Pydantic v2, httpx (reserved for future). |
| V — `gh` for GitHub | PASS | `bis/github.py` is the sole `gh` caller; no SDK; no token read. |

No new violations. Proceeding to Phase 1.
