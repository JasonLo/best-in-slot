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

### User Story 3 - Run steps 1 and 2 from a conversational skill (Priority: P3 — nice to have)

The mine-and-propose phase and the confirm phase (i.e. User Story 1) are accessible from a Claude skill, not only from the CLI. The user can type a slash command or natural-language phrase to start the bootstrap inside a conversation, walk through the slot proposals interactively, and end with a confirmed structure — all without leaving the chat.

**Why this priority**: User explicitly marked this as "nice to have." It does not unlock new capability; it changes the entry surface from terminal to conversation. Shipping P1 + P2 alone is still valuable; adding P3 lowers the barrier for users who live in Claude Code.

**Independent Test**: From a conversation, the user invokes the bootstrap skill and completes a full mine → propose → confirm round trip, persisting the same artifacts the CLI bootstrap would produce.

**Acceptance Scenarios**:

1. **Given** no slots exist, **When** the user invokes the bootstrap skill conversationally, **Then** they reach a confirmed slot structure without typing any CLI commands.
2. **Given** the user runs the CLI bootstrap and the skill bootstrap on the same project, **When** comparing the resulting state, **Then** the underlying artifacts are equivalent — only the input surface differs.

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

## Assumptions

- The user has a GitHub account and authenticated CLI access (e.g., a working `gh` session); the system relies on the existing auth surface rather than introducing its own credential flow.
- "Best-in-slot" categories are not pre-fixed: the proposal phase may infer categories from the data, draw from configured categories, or both — the spec does not constrain how the inference works, only what the user sees and can act on.
- Each inferred category carries a category-type tag of `language`, `framework`, or `tooling`, used by FR-014 to drive walk-through ordering. The exact taxonomy mapping (which packages count as which type) is an implementation decision for `/speckit-plan`; only the three-tier grouping is fixed here.
- The trailing-window length is fixed at 3 years per the user's description. A future iteration may make it configurable; this iteration treats it as a constant.
- The existing `/deep-dive` skill is treated as a black box: it accepts a slot and produces enrichment content; this spec does not redefine its behavior.
- The bootstrap is interactive by design — there is no fully automated, no-confirmation mode in this iteration. Every slot crosses the user's eyes before it lands.
- "Best-guess" is the operative word in step 1: the proposal is an opinionated draft, not a finished structure. The confirmation step (User Story 1) is where it becomes real.
- Both the CLI and the skill entry point produce identical underlying artifacts; the skill is purely a different surface, not a different feature.
