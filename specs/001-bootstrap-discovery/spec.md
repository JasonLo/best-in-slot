# Feature Specification: Bootstrap Discovery Pipeline

**Feature Branch**: `001-bootstrap-discovery`

**Created**: 2026-05-22

**Status**: Draft

**Input**: User description: "The discovery is a multistep process. 1. roughly obtain recently used tools in the past 3 years from user's gh repos (include orgs, or private, and public). Based on best guess, suggest a rought best-in-slot structure. 2. Ask user to confirm each slot 3. Refine each slot with /deep-dive skill. Nice to have is adding skill to do 1 and 2. I already have /deep-dive"

## Clarifications

### Session 2026-05-22

- Q: When the user chooses "change" for a slot, what alternatives can they select? → A: Observed alternatives are the default surface, but free-form override is accepted (any package the user names).
- Q: What private-repo data may cross a trust boundary (e.g., be sent to an LLM) during mining and category inference? → A: Package/manifest names, frequencies, and recency timestamps may be sent to the LLM; raw repo content (source files, README bodies, file contents) never leaves the machine.
- Q: How does a deferred slot return to the user's attention? → A: Automatically resurfaces on the next bootstrap run; no timer or cooldown, just a flag.
- Q: In what order are slot proposals presented during the walk-through? → A: Grouped by category type — languages first, then frameworks, then tooling — with evidence-strength (strongest first) as the tiebreaker within each group.
- Q: If mining is interrupted (crash, abort) partway through, how is its work preserved? → A: Per-repo cache with a short TTL (~24h); retries within the window skip already-scanned repos, no first-class resumable-job state.
- Q: Should `bis init walk` also present the US6 structure-confirmation step? → A: Yes — confirm step appears in both `bis init` and `bis init walk`; `bis init walk` accepts a `--skip-confirm` flag for the skill flow (which already called `taxonomy-review`).
- Q: How does the US6 reshape sub-loop terminate? → A: Single inner loop — shows overview, accepts repeated `split/merge/rename/drop/add` actions, exits only on explicit `done` (then proceeds to walk).
- Q: What is the SC-013 measurement denominator? → A: Conditional — measure across runs with ≥1 edit only. SC-013 = (edits at confirm phase) / (total edits across qualifying runs) ≥ 95%.
- Q: Should the US6 confirm prompt be skipped when no reshape is plausible (e.g., single slot)? → A: No — always show overview + prompt unconditionally, but `looks good` is the default; pressing Enter accepts and proceeds. Reshape requires explicit typing.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Propose a best-in-slot structure from my recent repo history (Priority: P1)

A user with a GitHub presence — public repos, private repos, and member organizations — wants the system to look at the tools they've actually used in the last three years and produce a best-guess best-in-slot structure: a category, a leading pick, and the evidence that supports it. They then walk through the proposal one slot at a time and accept, change, or skip each pick. At the end of the flow, the user has a confirmed slot set that reflects how they actually work, not a generic template.

**Why this priority**: Without this story, the user has no starting structure — every other workflow in the project assumes slots already exist. This is the on-ramp. Shipped alone, it is sufficient to take a new user from zero to a working slot set.

**Independent Test**: A user with no slots runs the bootstrap, reviews the proposed structure, confirms (or amends) each slot, and ends with a persisted set of slots that matches their decisions.

**Acceptance Scenarios**:

1. **Given** a user with repository activity in the trailing 3-year window, **When** the user initiates the bootstrap, **Then** the system produces a proposed slot structure with at least: a category label, a proposed pick, the count of repos that contributed, and the most recent contributing date for each slot.
2. **Given** a proposed slot structure, **When** the user walks through it, **Then** they can accept, change the pick to a named alternative, skip the slot, or defer the decision — and each decision is recorded.
3. **Given** the user has completed the walk-through, **When** the run ends, **Then** the confirmed slots are persisted as project artifacts in the same shape and location used by the rest of the project, so all other commands work against them without further setup.

---

### User Story 2 - Deepen each confirmed slot with /deep-dive (Priority: P2)

Once a slot is confirmed during the bootstrap walk-through, the user is offered the option to run the existing `/deep-dive` skill against it. Confirmed slots can be enriched immediately (one by one as they are confirmed) or queued and processed in a batch at the end of the walk-through. The resulting deep-dive output is attached to the slot so it survives the conversation.

**Why this priority**: Without this story the bootstrap still delivers value (a confirmed slot set), but each slot is then a blank entry. Chaining `/deep-dive` produces enriched slots in the same flow, removing a follow-up step the user would otherwise have to remember.

**Independent Test**: After confirming a slot during bootstrap, the user is offered `/deep-dive`; on accept, the deep-dive output is generated and persisted to that slot.

**Acceptance Scenarios**:

1. **Given** a freshly confirmed slot, **When** the user accepts the deep-dive prompt, **Then** the deep-dive skill is invoked for that slot and its output is persisted alongside the slot.
2. **Given** the user declines the deep-dive prompt for a slot, **When** the bootstrap continues, **Then** the slot is still persisted (without deep-dive content) and the user can run `/deep-dive` against it later without re-running the bootstrap.
3. **Given** a deep-dive invocation fails mid-batch, **When** the bootstrap continues, **Then** subsequent slots are not blocked and the failed slot is reported in the final summary.

---

### User Story 4 - Reshape the slot structure during bootstrap (Priority: P2)

A user walking through the bootstrap discovers that the proposed taxonomy itself is wrong — not the pick within a slot, but the slot's *shape*. The classic case: the bootstrap proposes one `python-tooling` slot that lumps `uv`, `ruff`, `ty`, `pytest`, `ipykernel` together where the winner is whichever is most frequent — but the user actually wants one slot per role (package-manager, linter-formatter, type-checker, test-runner, notebook-kernel). Today the user has to abort the walk-through and hand-edit `bis/categories.py`. US4 makes that conversational: at two scopes — a pre-walk taxonomy review and a per-slot inline action — the user can **split**, **merge**, **rename**, **drop**, or **add a custom** slot. Pick decisions then run against the rebuilt taxonomy.

**Why this priority**: Real-world bootstrap usage produced commit `3bc2482` ("split python-tooling into 5 sub-slots") — the user had to hand-edit `categories.py` mid-flight because the conversational flow had no affordance for it. Without US4, every taxonomy mismatch becomes a code edit. P2 because US1 still delivers value without it (users with a clean taxonomy don't need US4), but P2 is high because *one* mismatched slot is enough to force the hand-edit today.

**Independent Test**: From a fresh `slots/` directory, the user runs the bootstrap, splits one proposed slot into N sub-slots, merges two proposed slots into one, renames one slot, drops one slot, adds one custom slot the bootstrap didn't propose, and then walks through picks against the rebuilt taxonomy. The resulting `slots/*.yaml` set reflects the rebuilt structure; `slots/.bootstrap.yaml` contains a replayable `taxonomy_edits` log; no hand-edits to `bis/categories.py` were required.

**Acceptance Scenarios**:

1. **Given** a proposed slot that lumps multiple roles (e.g., `python-tooling` with uv + ruff + ty + pytest + ipykernel), **When** the user picks `split`, **Then** the system proposes a suggested partition (using the heuristic table) and, on user confirmation, replaces the one proposal with N sub-proposals — each carrying the evidence for its own member packages — and re-runs the FR-014 ordering against the rebuilt set.
2. **Given** two proposed slots the user considers redundant (e.g., `python-config` and `python-validation` for a user who treats them as one), **When** the user picks `merge` on one and supplies the other as the target, **Then** the two proposals collapse into one with unioned evidence (repo counts summed over disjoint contributing repos, most-recent = max, alternatives concatenated dedup) and the walk-through continues against the merged proposal.
3. **Given** a proposed slot whose category label the user dislikes (e.g., `databases` → `datastore`), **When** the user picks `rename`, **Then** the proposal's `category` field changes without touching evidence or members, and any subsequent pick decision writes `slots/<new-name>.yaml`.
4. **Given** a proposed slot the user considers not slot-worthy at all, **When** the user picks `drop`, **Then** the proposal is removed from the walk-through queue entirely (distinct from `skip`, which leaves the category but defers the pick) and no `slots/<cat>.yaml` is written for it.
5. **Given** the user wants a slot the bootstrap didn't propose (e.g., `infra` with `terraform`), **When** the user picks `add` and supplies the category name, category type, and pick, **Then** a `slots/<cat>.yaml` is written for the new slot and it appears in the rebuilt taxonomy as a fully-confirmed entry — no further accept/change prompt needed.
6. **Given** the user has aborted a walk-through after applying structural edits, **When** they re-run the bootstrap (fresh mining), **Then** the cached `taxonomy_edits` from `slots/.bootstrap.yaml` are replayed against the freshly-mined proposal set and the user is presented with the rebuilt taxonomy without being asked to redo the structural decisions.

---

### User Story 3 - Run steps 1 and 2 from a conversational skill (Priority: P3 — nice to have)

The mine-and-propose phase and the confirm phase (i.e. User Story 1) are accessible from a Claude skill, not only from the CLI. The user can type a slash command or natural-language phrase to start the bootstrap inside a conversation, walk through the slot proposals interactively, and end with a confirmed structure — all without leaving the chat.

**Why this priority**: User explicitly marked this as "nice to have." It does not unlock new capability; it changes the entry surface from terminal to conversation. Shipping P1 + P2 alone is still valuable; adding P3 lowers the barrier for users who live in Claude Code.

**Independent Test**: From a conversation, the user invokes the bootstrap skill and completes a full mine → propose → confirm round trip, persisting the same artifacts the CLI bootstrap would produce.

**Acceptance Scenarios**:

1. **Given** no slots exist, **When** the user invokes the bootstrap skill conversationally, **Then** they reach a confirmed slot structure without typing any CLI commands.
2. **Given** the user runs the CLI bootstrap and the skill bootstrap on the same project, **When** comparing the resulting state, **Then** the underlying artifacts are equivalent — only the input surface differs.

---

### User Story 5 - Fast hand-off to a local walk-through (Priority: P1 — UX refinement on the MVP path)

A user starts the bootstrap from `/bis-bootstrap` and expects the per-slot decisions to feel snappy — sub-second response between proposals — not 5–15 seconds per slot the way an LLM-driven conversational loop produces. The system splits the work along the FR-013 trust boundary: the LLM handles upfront mining + category-inference-on-unknowns (where its judgment is genuinely useful), then hands off to a local fast TTY walk-through driven by `questionary` (arrow keys + Enter, no LLM in the loop), then re-engages once at the end for batched `/deep-dive` chaining. From the user's perspective, a bootstrap session ends up costing ≤3 LLM turns instead of one-per-slot, and the per-slot decisions complete at native terminal speed.

**Why this priority**: Reported as a current pain point on 2026-05-22: "current bis-bootstrap workflow is way too slow, user spend much time just waiting." The per-slot LLM loop adds no judgment value — the user already knows their preferred pick — but it costs 2–4 minutes of cumulative latency per session at typical scale (~12 slots × ~5–15s/turn). US5 collapses that latency to ≤30 seconds of LLM-active time per session by redistributing the work. P1 because it materially affects the existing MVP UX — every bootstrap session benefits immediately once shipped.

**Independent Test**: From `/bis-bootstrap` against a fixture proposal set, verify (a) the conversation produces ≤3 LLM turns (mine → handoff → final summary), (b) per-slot decisions happen in a local `questionary` UI driven by keypresses, (c) system-side per-decision latency p95 < 200ms (measured via a deterministic walk adapter), (d) the resulting `slots/*.yaml` set is byte-identical to the prior LLM-in-loop flow modulo `decided_at` timestamps.

**Acceptance Scenarios**:

1. **Given** a proposed slot set produced by mining, **When** the bootstrap skill runs, **Then** it executes `bis init mine` once (one LLM turn), surfaces a one-line "Mined N proposals — hand off to local walk?" prompt (the user replies once), and `exec`s `bis init walk` in the user's terminal — at which point the LLM is out of the loop until the walk completes.
2. **Given** the local `bis init walk` is running, **When** the user picks an action on a slot, **Then** the next slot's prompt appears with no perceptible delay (system-side latency < 200ms), and the user can drive accept/change/skip/defer entirely with arrow keys + Enter without typing free-form text unless they choose "change → freeform".
3. **Given** the walk-through completes, **When** the skill re-engages, **Then** it reads `slots/.bootstrap.yaml` for the run summary and offers `/deep-dive` once over the full list of confirmed slots with a single `[all/none/select]` prompt — no per-slot deep-dive prompt.
4. **Given** the user `Ctrl-C`s mid-walk, **When** they re-run `bis init walk` later, **Then** the same pending proposals are presented (no re-mining required) because `pending_proposals` was persisted into `slots/.bootstrap.yaml` by the earlier `bis init mine` call.
5. **Given** a user runs the pure-CLI path (`bis init` with no flags), **When** they walk through the proposals, **Then** they see the same snappy `questionary` UX as the skill-driven path — the underlying `WalkController` is shared, the skill is purely a different entry point.

---

### User Story 6 - Confirm slot structure before per-slot picks (Priority: P1)

A user running `bis init` (default flow) or `bis init walk` (post-mine) wants to see the overall slot *structure* before being asked to pick within each slot. Today the CLI mines, proposes, and drops the user straight into per-slot prompts — if the taxonomy is wrong (one of US4's classic cases: `python-tooling` lumped, or a missing `infra` slot), the user has to abort or live with it. US6 promotes US4's taxonomy review from an opt-in skill subcommand to a first-class step of every interactive bootstrap entry point: after mining and before any per-slot prompt, the user sees the structure overview (category, type, members, suggested splits) and either accepts it (Enter) or enters a reshape sub-loop that uses the same split/merge/rename/drop/add primitives US4 introduced.

**Why this priority**: US4 made structural edits possible. US6 makes them discoverable in the default flow. P1 because it changes the default UX of the MVP entry point — every terminal-driven bootstrap session sees the new step, and the existing skill flow (US3/US5) continues to work unchanged (the skill already calls `taxonomy-review` upfront, so `bis init walk --skip-confirm` lets it opt out).

**Independent Test**: Run `uv run bis init` (no flags) against a fixture proposal set. Verify (a) after mining, a structure-overview block prints listing each proposed category with type/members/suggest_split_into, (b) the user is prompted `[looks good / reshape]` with `looks good` as the default BEFORE any per-slot prompt appears, (c) on Enter, the walk-through proceeds; on `reshape`, the user can apply multiple structural edits in a single inner loop and the walk-through iterates the rebuilt proposal set in FR-014 order, (d) `bis init walk --skip-confirm` bypasses the prompt for the skill flow, (e) `--batch --json` mode emits a `proposed_structure_overview` field but performs no prompt.

**Acceptance Scenarios**:

1. **Given** a fresh `slots/` directory, **When** the user runs `uv run bis init`, **Then** the CLI prints a structure overview block after mining and before any per-slot prompt, with `[looks good / reshape]` as the next prompt and `looks good` as the default — pressing Enter accepts.
2. **Given** the user picks `reshape`, **When** they apply two structural edits (e.g., one `split` and one `rename`) and then issue `done`, **Then** both edits are recorded in `slots/.bootstrap.yaml:taxonomy_edits` with `applied_at_phase == "confirm"`, only one trip through the outer `[looks good / reshape]` prompt is needed, and the subsequent walk-through iterates the rebuilt proposal set in FR-014 order.
3. **Given** the skill flow runs `bis init mine` followed by `bis init walk --skip-confirm`, **When** the walk subcommand starts, **Then** NO confirm prompt fires (the skill already called `taxonomy-review`), preserving FR-024's byte-identical-result invariant.
4. **Given** a trivial proposal set (single proposal, no split possible), **When** `bis init` runs, **Then** the overview + prompt still appear (FR-025 is unconditional), but Enter immediately accepts and the walk begins — no carve-out heuristic.
5. **Given** `bis init --batch --json` runs, **When** the JSON payload is emitted, **Then** it includes a `proposed_structure_overview` field alongside the existing `proposals` field, and no interactive prompt is presented.

---

### Edge Cases

- **Sparse signal**: The user has very few repos in the 3-year window. Surface "low confidence — only N repos contributed" rather than fabricating slots from a single data point.
- **Over-weighted ecosystem**: A user with many small Python repos shouldn't get a Python-only slot list. The proposal should reflect category diversity, not raw frequency.
- **Tools that aren't slot-worthy**: Some tools that appear in dependency files don't make sense as slots (transitive utility libraries, polyfills). The proposal should skip these rather than offering a category for them.
- **Conflicting picks within a category**: User has used multiple competing tools (e.g., FastAPI in some repos, Django in others). The proposal should surface both and let the user choose, not silently pick the most frequent.
- **Existing slots present**: The user has already run a bootstrap before. The system must detect this and explicitly ask: merge, replace, or skip — never overwrite silently.
- **Org or private-repo access denied**: The GitHub token lacks scope for some sources. The system should continue with reduced coverage and clearly report which sources were skipped and why.
- **Deep-dive failure on one slot**: Should not block the rest of the walk-through. Report at the end.
- **User aborts mid-walk-through**: Already-confirmed slots up to the abort point should still be persisted; un-decided slots are left in a deferred state, not lost.
- **No repository activity in the 3-year window**: Surface "no recent activity found — broaden the window or seed manually" rather than producing an empty slot set silently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST scan the user's GitHub presence — public repositories, private repositories the user can access, and repositories in organizations the user is a member of — for repository activity within the trailing 3-year window.
- **FR-002**: The system MUST parse each scanned repository for tool/dependency signals using whatever manifest formats are present, and aggregate the signals into a per-tool frequency and recency record.
- **FR-003**: The system MUST translate the aggregated tool signals into a best-guess best-in-slot proposal containing, for each proposed slot: a category label, a proposed pick, the count of contributing repos, the most recent contributing date, and (when applicable) any plausible alternatives observed in the same data.
- **FR-004**: The system MUST present the proposal to the user one slot at a time, with four available actions per slot: accept the pick, change the pick to a named alternative, skip the slot, or defer the decision. When the user chooses "change", the system MUST default to surfacing the observed-in-history alternatives for that category as the suggested list, AND MUST also accept a free-form package name the user types — even one not present in their repo history.
- **FR-005**: For each confirmed slot, the system MUST offer the user the option to run the existing `/deep-dive` skill against that slot, and on user assent, invoke it and persist the resulting deep-dive output alongside the slot.
- **FR-006**: The system MUST persist all confirmed slots — and their deep-dive output where applicable — into the same project artifacts used by the rest of the project, so that other commands operate against them without further setup.
- **FR-007**: When prior slot state already exists in the project, the system MUST detect it and require an explicit user choice between merge, replace, or skip before any state change.
- **FR-008**: When GitHub access is partial (org or private-repo access denied, scope missing, rate limits hit), the system MUST continue with reduced coverage and report which sources were skipped, with the reason, in the run's final summary.
- **FR-009**: The system MUST surface, alongside each proposed slot, the count of repos and the most recent contributing date that produced the proposal, so the user can judge signal strength before deciding.
- **FR-010**: The mine-and-propose phase and the per-slot confirmation walk-through MUST be invokable both from the existing CLI and from a Claude skill entry point. The skill entry point is in scope but lower priority (see User Story 3).
- **FR-011**: A deep-dive failure on any single slot MUST NOT halt the rest of the walk-through; the failure MUST be reported in the run's final summary.
- **FR-012**: When the user aborts the walk-through, already-confirmed slots MUST be persisted; undecided slots MUST be retained in a deferred state for a future run, not silently discarded. On the next invocation of the bootstrap, deferred slots MUST automatically be re-presented to the user in the walk-through — no cooldown, no separate command required to revisit them.
- **FR-013**: Data crossing a trust boundary (e.g., sent to an LLM) during mining or category inference MUST be limited to package/manifest names, aggregated frequencies, and recency timestamps. Raw repository content — source files, README bodies, manifest excerpts beyond the parsed name list — MUST NOT leave the user's machine as part of this feature.
- **FR-014**: The walk-through MUST present slot proposals grouped by category type in the order: languages → frameworks → tooling. Within each group, proposals MUST be ordered by evidence-strength (strongest first), so the ordering is deterministic given the same input data.
- **FR-015**: The mining phase MUST cache per-repo scan results locally with a TTL of approximately 24 hours. On a re-run within the TTL, already-scanned repos MUST be skipped (their cached signals reused) so a crash or abort during mining does not force a full re-scan. The system is not required to support first-class job checkpoints or indefinite-gap resumption.
- **FR-016**: The walk-through MUST support five structural actions per proposed slot in addition to the four pick actions (accept / change / skip / defer): **split** (replace one proposal with N sub-proposals — system suggests a partition using the heuristic table or accepts a user-supplied list), **merge** (collapse this proposal into another with unioned evidence), **rename** (change the category label without changing membership), **drop** (remove the proposal from the queue entirely — distinct from skip), and **add** (insert a custom slot not present in the proposal set, with user-supplied name, type, and pick).
- **FR-017**: Before the per-slot walk-through begins, the system MUST offer the user a one-shot **taxonomy review** — an overview of the full proposal list with each proposal's category, type, members, and (where the heuristic table can offer one) a suggested split. The user MAY skip the review in `--batch` mode or via `bis init walk --skip-confirm`; in all other interactive entry points (default `bis init`, `bis init walk` without `--skip-confirm`) the review MUST surface (see FR-025).
- **FR-018**: All structural changes applied during a run MUST be persisted as an append-only `taxonomy_edits` log in `slots/.bootstrap.yaml`. On the next bootstrap run, after fresh mining, the system MUST replay these edits against the new proposal set before presenting the walk-through — so an aborted-mid-reshape run resumes against the rebuilt taxonomy without re-prompting the user for the same structural decisions.
- **FR-019**: Structural actions MUST preserve evidence: **merge** unions `evidence_repo_count` over disjoint contributing-repo sets (no naive sum that double-counts), `evidence_most_recent` = max, alternatives = ordered dedup union, `category_type` must match across merged inputs (mismatch is a user-facing error); **rename** is identity-on-evidence; **split** partitions evidence by member-package's heuristic sub-category; **drop** removes evidence with no residual; **add** carries user-supplied evidence (initialised as `evidence_repo_count = 1`, `most_recent = now`).
- **FR-020**: Structural-action suggestions (e.g., `suggest_split` proposing how to partition a slot) MUST be **deterministic and local** — derived only from `bis/categories.py:CATEGORY_TABLE` and the in-memory proposal set. No structural-action helper MAY call the LLM. This preserves the FR-013 trust boundary (no new payload leaves the machine for structure decisions).
- **FR-021**: The system MUST expose a mining-only CLI mode (`bis init mine --json`) that runs mining, proposal-building, and `taxonomy_edits` replay, persists the resulting proposal set into `slots/.bootstrap.yaml` under a `pending_proposals` field, and exits without entering the walk-through. This is the skill's handoff payload — the LLM uses it to produce a one-line summary, then surrenders control of the walk to the local CLI.
- **FR-022**: The system MUST expose a fast local interactive walk-through (`bis init walk`) that reads `pending_proposals` from `slots/.bootstrap.yaml` (or from stdin via `--from-stdin`) and drives the per-slot decisions using a `questionary`-style TTY UX — arrow keys + Enter for action selection, free-form text input only when the user picks "change → freeform". System-side per-slot decision latency MUST be sub-second.
- **FR-023**: The bootstrap skill (`skills/bis-bootstrap/SKILL.md`) MUST minimise LLM turns: ≤3 turns per session — one for mining, one for the handoff prompt, one for the final summary + batched `/deep-dive` offer. Per-slot conversational iteration during the walk-through is forbidden — that responsibility belongs to the local `bis init walk` command.
- **FR-024**: The handoff transport MUST be process-level: the skill `exec`s `bis init walk` in the user's terminal (or instructs the user to run it) rather than driving the walk via tool calls. The resulting slot state MUST be byte-identical to a pure-CLI `bis init` run against the same proposal set, modulo `decided_at` timestamps and `run_id`. The trust-boundary invariant from FR-013 is unchanged: the handoff introduces no new LLM-bound payload type.
- **FR-025**: Both the default `bis init` flow AND `bis init walk` MUST present a **structure-confirmation step** after mining (or after loading `pending_proposals`) and before any per-slot prompt. The step shows the same overview produced by `bis init taxonomy-review` and prompts the user with `[looks good / reshape]` where `looks good` is the default — pressing Enter accepts and proceeds. The overview is shown **unconditionally**, including for trivial proposal sets (single proposal, no possible split); no heuristic carve-out is permitted. `bis init walk` MUST accept a `--skip-confirm` flag that bypasses the step for the skill flow (which already calls `taxonomy-review`); the flag MUST NOT exist on the default `bis init` entry point (the structure-confirmation step is non-skippable there outside `--batch`).
- **FR-026**: The structure-confirmation step MUST reuse the same `split / merge / rename / drop / add` primitives introduced by US4 (FR-016) — no new structural action is introduced. On `reshape`, the system MUST enter a **single inner loop** that accepts repeated structural actions, re-displays the overview after each edit, and exits only on an explicit `done` action. All edits applied during the step MUST be appended to `taxonomy_edits` (per FR-018) with `applied_at_phase == "confirm"` to distinguish them from edits applied during the per-slot walk (`applied_at_phase == "walk"`).

### Key Entities *(include if feature involves data)*

- **Tool signal**: A single observation that a particular tool appears in a particular repository, tagged with the repo identity and the most recent timestamp that supports recency.
- **Slot proposal**: A draft slot derived from aggregated tool signals — category, proposed pick, evidence (repo count, recency, alternatives observed), and a confidence-relevant qualifier (e.g., "low evidence", "conflicting alternatives").
- **Slot decision**: The user's outcome for one proposal — accept / change / skip / defer — plus, where applicable, the named replacement pick.
- **Deep-dive enrichment**: The artifact produced by chaining the existing `/deep-dive` skill against a confirmed slot, persisted alongside the slot record.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time user can go from zero slots to a fully confirmed, deep-dived slot set in a single conversation in under 30 minutes for a user with ≤50 active repos in the 3-year window.
- **SC-002**: The proposed slot structure earns an explicit "accept" decision on at least 70% of proposed slots without modification, indicating the proposal reflects the user's actual stack.
- **SC-003**: Every persisted slot from a bootstrap run contains the contributing evidence (repo count, most recent date) that produced the proposal, so future audits can trace why the slot was created.
- **SC-004**: When some GitHub sources are inaccessible, the run completes anyway and the final summary names every skipped source and the reason, 100% of the time — the run never silently drops sources.
- **SC-005**: A user re-running the bootstrap on a project that already has slots is presented with an explicit merge/replace/skip choice before any state change, 100% of the time — existing data is never overwritten silently.
- **SC-006**: Total wall-clock time the user spends *waiting* on system mining/processing during the run — i.e. with no input requested from them — is under 5 minutes for a user with ≤50 repos in the 3-year window.
- **SC-007**: A user who aborts the walk-through partway through can resume in a later session and finds every already-confirmed slot persisted and every undecided slot still pending — zero confirmed work is lost.
- **SC-008**: A security-conscious user can run the bootstrap on a project containing private repos and confirm — by inspecting whatever the tool would send externally — that no raw repository content is included, 100% of the time.
- **SC-009**: A user who restarts the bootstrap within 24 hours of a prior aborted run completes the mining phase in under 25% of the wall-clock time the first run took (i.e., the cache makes restarts substantively cheaper, not just incrementally so).
- **SC-010**: A user whose proposed taxonomy needs at least one structural change (split, merge, rename, drop, or add) can complete that change conversationally — without editing `bis/categories.py` or any other source file — 100% of the time. Verified against the commit `3bc2482` reshape scenario: split `python-tooling` into 5 sub-slots end-to-end from the skill, no code edits.
- **SC-011**: System-side per-slot decision latency in the local walk-through (`bis init walk`) is p95 < 200ms — measured from `WalkController.present_proposal` entry to `apply_decision` return, with a deterministic adapter that does not touch the TTY. Enforced by a CI regression test against a 20-proposal fixture.
- **SC-012**: Total LLM-active wall-clock time in a `/bis-bootstrap` session is < 30 seconds for sessions with ≤15 slots — measured as the sum of (mining turn + handoff turn + summary turn). The prior conversational-loop baseline at the same scale is ≥2 minutes; SC-012 represents at least a 4× reduction in user-visible latency for the median session.
- **SC-013**: Across all runs that applied **≥1 structural edit** (runs with zero edits are excluded from the denominator), at least **95% of `taxonomy_edits` entries** carry `applied_at_phase == "confirm"` — measured by inspecting the run state. The remaining ≤5% may carry `applied_at_phase == "walk"` (edits made mid per-slot loop) or `"post_walk"`. SC-013 measures *user behaviour given they wanted to reshape*: that the confirmation step is where reshape happens, not an afterthought during the walk.

## Assumptions

- The user has a GitHub account and authenticated CLI access (e.g., a working `gh` session); the system relies on the existing auth surface rather than introducing its own credential flow.
- "Best-in-slot" categories are not pre-fixed: the proposal phase may infer categories from the data, draw from configured categories, or both — the spec does not constrain how the inference works, only what the user sees and can act on.
- Each inferred category carries a category-type tag of `language`, `framework`, or `tooling`, used by FR-014 to drive walk-through ordering. The exact taxonomy mapping (which packages count as which type) is an implementation decision for `/speckit-plan`; only the three-tier grouping is fixed here.
- The trailing-window length is fixed at 3 years per the user's description. A future iteration may make it configurable; this iteration treats it as a constant.
- The existing `/deep-dive` skill is treated as a black box: it accepts a slot and produces enrichment content; this spec does not redefine its behavior.
- The bootstrap is interactive by design — there is no fully automated, no-confirmation mode in this iteration. Every slot crosses the user's eyes before it lands.
- "Best-guess" is the operative word in step 1: the proposal is an opinionated draft, not a finished structure. The confirmation step (User Story 1) is where it becomes real.
- Both the CLI and the skill entry point produce identical underlying artifacts; the skill is purely a different surface, not a different feature.
