# Feature Specification: Skill-Driven Discovery UX

**Feature Branch**: `001-skill-driven-discovery`

**Created**: 2026-05-22

**Status**: Draft

**Input**: User description: "Improve best-in-slot discovery ux, link it or create claude skills to act as the main user interface."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Surface what's stale in my stack (Priority: P1)

The user opens a conversation and asks, in plain language or via a slash command, "what's stale in my stack?" The system identifies every slot considered stale, ranks them by how far out of date they are and how much the user relies on them, and presents a short, human-readable summary for each — including *why* it is stale and what plausible replacements exist. No raw JSON, no CLI flag knowledge required.

**Why this priority**: This is the entry point users hit first. Today the answer to "what should I look at next?" lives in a JSON blob; making it conversational unlocks the rest of the workflow. With just this story shipped, a user can audit their stack faster than today and still complete switches via the existing CLI.

**Independent Test**: From a fresh conversation, the user invokes the discovery entry point and receives a ranked, prose summary of every stale slot with a clear "what's next" prompt — without typing any CLI commands.

**Acceptance Scenarios**:

1. **Given** a project with at least one stale slot, **When** the user invokes the discovery entry point, **Then** the response lists each stale slot with: the current pick, why it is considered stale, top alternative candidate(s), and a suggested next action.
2. **Given** a project with no stale slots, **When** the user invokes discovery, **Then** the response confirms freshness and offers a constructive next step (e.g., deep-dive on a chosen slot).
3. **Given** the project has never been profiled, **When** the user invokes discovery, **Then** the response detects the missing prerequisite and walks the user through the one step needed to unblock.

---

### User Story 2 - Walk me through evaluating one alternative (Priority: P2)

For a single slot, the user wants a guided evaluation of a specific candidate — or of the system's top suggestion — that combines scoring data with qualitative reasoning (docs scan, ecosystem fit, migration considerations) and ends with an actionable recommendation. If the user accepts, the slot is updated and the rationale is persisted; if not, the candidate is recorded as considered-and-rejected.

**Why this priority**: This is where the qualitative value-add lives. Scoring alone can't tell the user whether a switch is worth it; this story is where Claude reads docs, weighs trade-offs, and produces a defensible recommendation.

**Independent Test**: From a conversation, the user picks any slot and asks "should I move from X to Y?" The system returns a recommendation with cited evidence, an explicit confirmation step, and — on approval — persists the change with the rationale.

**Acceptance Scenarios**:

1. **Given** a stale slot with at least one candidate, **When** the user asks to evaluate a candidate, **Then** the system returns a recommendation that includes scoring, pros, cons, citations the user can verify, and a yes/no confirmation prompt.
2. **Given** the user confirms a switch, **When** the system records it, **Then** the slot's history captures the new pick, the rationale, and a timestamp.
3. **Given** the user declines a switch, **When** the system records the decision, **Then** the candidate is logged as considered-but-rejected so it does not get re-recommended without new evidence.

---

### User Story 3 - Refresh my whole stack in one session (Priority: P3)

The user wants to triage every stale slot back-to-back without re-invoking discovery each time. The system walks them through each stale slot in priority order, offering at each step: accept the recommendation, defer, skip permanently (pin), or open a deeper look — until the queue is empty.

**Why this priority**: This is the "spring cleaning" flow. It compounds the value of P1 and P2 but is not required to deliver value on its own.

**Independent Test**: From a conversation, the user invokes a stack-refresh entry point; the system processes every stale slot in turn, persists each decision, and reports a final summary.

**Acceptance Scenarios**:

1. **Given** multiple stale slots, **When** the user invokes the refresh flow, **Then** the system iterates through them in priority order without requiring the user to restate context.
2. **Given** the user opts to defer a slot, **When** the flow continues, **Then** the deferred slot is recorded with a defer-until signal so future discovery does not nag immediately.
3. **Given** the user pins a slot, **When** the flow continues, **Then** future discovery omits the pinned slot until the pin is explicitly cleared.

---

### Edge Cases

- **No stale slots**: Confirm freshness clearly; do not invent work.
- **Missing profile or no slots initialized**: Detect, explain, and guide the user to the one prerequisite command — never fail with a stack trace.
- **Slot with no plausible alternative**: Say so plainly ("the current pick is still the strongest candidate in this category"); do not invent low-quality alternatives.
- **Registry/network unavailable**: Degrade gracefully — surface what is already known from local data, flag what could not be refreshed, and let the user proceed with caveats.
- **Conflicting slots that should move together** (e.g., a web framework and its companion ORM): Flag the coupling so the user is aware before switching one in isolation.
- **User invokes discovery from a non-project directory**: Detect the missing project artifacts and explain rather than error.
- **Concurrent CLI and skill use**: A switch performed via the CLI between two skill invocations must not be silently overwritten by the skill.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A user-facing entry point — invokable both by slash command and by natural-language phrasing — MUST let a user discover stale slots without typing any CLI commands.
- **FR-002**: Discovery results MUST be presented as ranked, human-readable summaries with reasoning, not as raw structured data.
- **FR-003**: For each surfaced stale slot, the user MUST be able to drill into a guided evaluation of at least one candidate within the same conversation.
- **FR-004**: Every recommendation MUST cite the basis for its judgment (user-repo usage signals, registry signals, maintenance signals, ecosystem fit) in a form the user can independently verify.
- **FR-005**: Users MUST be able to act on a recommendation — apply, defer, or reject — from within the conversation, with an explicit confirmation step before any state change.
- **FR-006**: The system MUST detect missing prerequisites (no profile, no slots, empty category) and guide the user to the smallest next step that unblocks them.
- **FR-007**: The skill-based UX MUST coexist with the existing CLI; direct CLI invocations and skill-mediated invocations MUST produce identical underlying project state.
- **FR-008**: The outcome of every evaluation — accept, defer, reject, or pin — MUST be persisted to project artifacts so it survives the conversation and informs future discovery.
- **FR-009**: The system MUST avoid re-recommending a candidate that was recently rejected unless meaningfully new evidence justifies revisiting it.
- **FR-010**: When a switch is applied via a skill, the persisted history entry MUST include a non-empty, human-written or system-generated rationale, never an empty reason.

### Key Entities *(include if feature involves data)*

- **Stale-slot summary**: A surfaced view of a tech-category slot whose current pick is judged out of date or worth revisiting; includes the current pick, why it surfaced, and ranked candidates.
- **Candidate evaluation**: A reasoned comparison of one alternative against the current pick; produces a recommendation, cited evidence, and a user-actionable confirmation.
- **Decision record**: The persisted outcome of an evaluation — accept, defer, reject, or pin — attached to the slot's history.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can audit every stale slot in their stack and decide a next action for each in a single conversation in under 10 minutes.
- **SC-002**: A user new to the project can complete a discover → evaluate → switch round trip without reading any CLI reference documentation.
- **SC-003**: 100% of slot switches initiated via the skill UX carry a non-empty rationale in the slot's persisted history.
- **SC-004**: Every recommendation surfaced by the skill UX includes at least one citation (a repo, registry page, release note, or documentation link) the user can independently verify.
- **SC-005**: Re-running discovery immediately after a session yields zero re-recommendations of candidates the user just rejected or deferred.
- **SC-006**: When prerequisites (profile, slots) are missing, the system reaches "user knows the one next command to run" in a single response 100% of the time — never failing with an unhandled error.

## Assumptions

- The existing `bis` CLI remains the source of truth for slot state, scoring, and persistence; skills front-end it rather than replacing it.
- Users primarily interact through Claude Code; the CLI remains supported for power users and scripting but is not the primary entry point.
- Skills follow the established repository pattern: each is a self-contained unit with a clear trigger, invoking the underlying engine and layering qualitative judgment on top.
- A user has run profile and init at least once before invoking discovery — or the discovery skill detects the gap and guides them there.
- Network access to package registries and the user's git host is available during discovery; graceful degradation covers the offline case but is not the steady-state assumption.
- "Stale" continues to be determined by the existing project-wide threshold configuration; this feature does not redefine staleness, only surfaces it differently.
- Switches always require explicit user confirmation; there is no autonomous-switch mode in this iteration.
- Deep-dive (single-tool) functionality already exists and is complementary — discovery is whole-stack triage; deep-dive is single-slot depth. Discovery may suggest a deep-dive as a next step, but does not duplicate its work.
