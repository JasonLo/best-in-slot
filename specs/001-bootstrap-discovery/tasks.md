---

description: "Task list for Bootstrap Discovery Pipeline implementation"
---

# Tasks: Bootstrap Discovery Pipeline

**Input**: Design documents from `/specs/001-bootstrap-discovery/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md (all present)

**Tests**: Included. The plan and constitution both call for `tests/contract/`, `tests/integration/`, `tests/unit/`; the project mandates test-first development for new modules. Test tasks are written FIRST per phase and must FAIL before the matching implementation lands.

**Organization**: Tasks are grouped by user story (US1 → US2 → US3) so each story is independently shippable.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Task can run in parallel (different files, no incomplete dependencies)
- **[Story]**: Maps to a user story (US1/US2/US3) from spec.md
- Every task has a concrete file path

## Path Conventions

Single-project Python CLI. Source under `bis/`, tests under `tests/`, skills under `skills/`, slot data under `slots/`. All paths below are repo-root-relative.

## Status legend

- `[x]` complete
- `[~]` partial / superseded by adjacent task (kept for traceability)
- `[ ]` open
- `[-]` won't-do (rationale inline)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Bring the Python toolchain online; remove cruft from a prior aborted scaffold.

- [x] T001 Create `pyproject.toml` at repo root with `requires-python = ">=3.14"`, `[project]` metadata, runtime deps (`typer>=0.12`, `pydantic>=2.7`, `httpx>=0.27`, `pyyaml>=6.0`), dev deps (`pytest>=8.0`, `pytest-asyncio>=0.23`, `ruff`, `ty`), `[project.scripts] bis = "bis.cli:app"`, and a `[tool.pytest.ini_options]` block pointing at `tests/`
- [x] T002 Update `.gitignore` at repo root to add `.bis/`, `profile.yaml`, `__pycache__/`, `*.egg-info`, `.pytest_cache/`
- [x] T003 [P] Delete the stale `bis/__pycache__/` directory (only `.pyc` files exist; no committed source — clean slate)
- [x] T004 [P] Create empty `bis/__init__.py` (package marker)
- [x] T005 [P] Create empty `tests/__init__.py`, `tests/contract/__init__.py`, `tests/integration/__init__.py`, `tests/unit/__init__.py`, `tests/fixtures/__init__.py`
- [x] T006 Run `uv sync` in repo root to materialize `.venv/` and `uv.lock` (depends on T001)

**Checkpoint**: `uv run python -c "import bis"` succeeds; `uv run pytest --collect-only` runs (collects 0 tests).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The minimum shared surface every user story needs — boundary types, settings, CLI skeleton, test infra.

**⚠️ CRITICAL**: No user-story work begins until this phase is complete.

- [x] T007 [P] Implement all 13 Pydantic v2 models in `bis/models.py` per `specs/001-bootstrap-discovery/data-model.md` (`RepoRef`, `ToolSignal`, `CachedRepoScan`, `ProfileSnapshot`, `SkippedSource`, `CategoryProposal`, `SafePayload`, `SafePayloadItem`, `SlotDecision`, `SlotState`, `EvidenceBlock`, `HistoryEntry`, `BootstrapRunState`), including the validators listed in the "Validation summary" table
- [x] T008 [P] Implement `bis/config.py` with a `Settings` Pydantic model and `load_settings(path: Path = Path("settings.yaml")) -> Settings` loader; default settings: 3y window, ~24h cache TTL, none of the optional fields required
- [x] T009 Implement `bis/cli.py` Typer app skeleton: `app = typer.Typer(no_args_is_help=True)`, a `__main__` guard, and a stub `@app.command()` for `bootstrap` that prints a "not yet implemented" message. Wired so `uv run bis --help` lists `bootstrap`.
- [x] T010 [P] Create `tests/conftest.py` with shared fixtures: `tmp_cache_root` (monkeypatches the `.bis/cache/` path to a `tmp_path`), `gh_stub` (registers a fake `gh` executable on `PATH` that reads canned JSON responses from `tests/fixtures/gh/`), `frozen_now` (freezes `datetime.now` for deterministic recency math)

**Checkpoint**: `uv run pytest tests/conftest.py --collect-only` succeeds; `uv run bis init` prints the stub message.

---

## Phase 3: User Story 1 — Propose + walk-through from repo history (Priority: P1) 🎯 MVP

**Goal**: A user with no slots runs `bis init`, sees a ranked proposal grouped languages → frameworks → tooling, walks through each slot with accept / change (observed or free-form) / skip / defer, and ends with persisted `slots/{category}.yaml` files. Mining is cached for ~24h. Privacy invariant FR-013 is enforced at the type level.

**Independent Test**: From an empty `slots/` directory, run `uv run bis init` against the `gh_stub` fixture; verify the expected slot YAMLs land, `slots/.bootstrap.yaml` records any deferrals, and the cache contains per-repo scan files.

### Tests for User Story 1 (write FIRST; ensure they FAIL before implementation)

- [x] T011 [P] [US1] Contract test: validate `bis init --json --batch` output against `specs/001-bootstrap-discovery/contracts/bootstrap.schema.json` in `tests/contract/test_bootstrap_json_output.py`
- [x] T012 [P] [US1] Contract test: validate `bis init confirm --json` output (one per action: accept/change/skip/defer) against the same schema's `confirm` branch in `tests/contract/test_bootstrap_confirm_output.py`
- [x] T013 [P] [US1] Contract test: validate walk-through event payloads against `specs/001-bootstrap-discovery/contracts/walkthrough-events.schema.json` in `tests/contract/test_walkthrough_events.py`
- [x] T014 [P] [US1] Integration test: end-to-end empty-slots bootstrap with `gh_stub` + fixture repo manifests; assert proposal contents, walk-through order (languages → frameworks → tooling), and persisted `slots/*.yaml` shape in `tests/integration/test_bootstrap_end_to_end.py`
- [x] T015 [P] [US1] Integration test: resume after abort — deferred slots persist in `slots/.bootstrap.yaml` and resurface at the top of the next run (FR-012, SC-007, R-9, R-11) in `tests/integration/test_bootstrap_resume_deferred.py`
- [x] T016 [P] [US1] Integration test: cache hit on re-run within TTL completes in ≤25% of cold-run wall time (SC-009) in `tests/integration/test_bootstrap_cache_hit.py`
- [x] T017 [P] [US1] Integration test: partial GitHub access (org access denied, scope missing) — run completes, `skipped_sources` populated, slots from accessible repos still proposed (FR-008, SC-004) in `tests/integration/test_bootstrap_partial_access.py`
- [x] T018 [P] [US1] Integration test: existing slots present — batch mode without `--on-existing` returns the `existing_state_unresolved` error envelope; interactive mode prompts; explicit `--on-existing=replace` records a `bootstrap-replace` history entry (FR-007, SC-005) in `tests/integration/test_bootstrap_existing_state.py`
- [x] T019 [P] [US1] Unit test: cache TTL — entries older than 24h are treated as miss; `scanner_version` mismatch is also a miss; valid cache hits round-trip identically (FR-015, R-1) in `tests/unit/test_cache_ttl.py`
- [x] T020 [P] [US1] Unit test: walk-through ordering — given a fixture proposal set, output is grouped languages → frameworks → tooling with evidence-strength descending within each group, deterministic across runs (FR-014, R-6) in `tests/unit/test_categories_ordering.py`
- [x] T021 [P] [US1] Unit test: category inference — heuristic table hits return without LLM call; unknown packages trigger LLM fallback receiving only a `SafePayload` (R-3) in `tests/unit/test_categories_inference.py`
- [x] T022 [P] [US1] Unit test: privacy scrubber no-leak invariant — serialise any `SafePayload`, assert it contains no manifest body, no README content, no path beyond the package layer (FR-013, SC-008, R-7) in `tests/unit/test_privacy_scrubber.py`
- [x] T023 [P] [US1] Unit test: manifest scanner parsers — one parametrised test per format (pyproject.toml, requirements.txt, package.json, go.mod, Cargo.toml, Gemfile) with golden fixtures in `tests/unit/test_scanner_parsers.py`
- [-] T024 [P] [US1] Fixture corpus: sample manifests for each parser in `tests/fixtures/manifests/{pyproject,requirements,package_json,go_mod,cargo,gemfile}/`; canned `gh` JSON responses for the integration tests in `tests/fixtures/gh/{list_repos,manifest_contents}.json` — won't-do: scanner tests embed manifest strings inline; integration tests mock `bis.cli.mine_profile` directly, so external fixture files would only add indirection. The `gh_stub` fixture in `conftest.py` is exercised by the partial-access test.

### Implementation for User Story 1

- [x] T025 [P] [US1] Implement `bis/scanner.py` with parsers for all 6 manifest formats. Each parser returns `dict[str, list[str]]` of normalised package names (lowercase, dashes-not-underscores for Python, scoped names preserved for npm). Expose `scan_manifest(path: Path, content: str) -> list[str]` and `KNOWN_FORMATS: set[str]`.
- [x] T026 [P] [US1] Implement `bis/github.py` with gh subprocess wrappers: `list_user_repos(window: timedelta) -> list[RepoRef]`, `list_org_repos(org: str, window: timedelta) -> list[RepoRef]`, `list_user_orgs() -> list[str]`, `get_manifest_paths(repo: RepoRef, formats: set[str]) -> list[str]`, `get_manifest_content(repo: RepoRef, path: str) -> str`. All call `gh api ...` via `subprocess.run`; never read `GITHUB_TOKEN`; degrade `gh` errors into `SkippedSource` records rather than raising.
- [x] T027 [P] [US1] Implement `bis/privacy.py`: `to_safe_payload(profile: ProfileSnapshot) -> SafePayload` and a module-level constant `SCANNER_VERSION` referenced by the cache. Function signature is the only allowed entry point to anything LLM-bound; raise `TypeError` if anything other than `ProfileSnapshot` is passed.
- [x] T028 [P] [US1] Implement `bis/cache.py`: `get_cached_scan(repo: RepoRef) -> CachedRepoScan | None` (returns None on miss/expiry/version-mismatch), `put_cached_scan(scan: CachedRepoScan) -> None`, `cache_root() -> Path` (defaults to `.bis/cache/repos/`, configurable via env). Per-repo file layout per R-1.
- [x] T029 [US1] Implement `bis/categories.py` (depends on T007, T027): (a) `CATEGORY_TABLE: dict[str, tuple[str, Literal["language","framework","tooling"]]]` heuristic table seeded with packages from the existing `slots/` content (fastapi, pandas, ruff, uv, etc.); (b) `infer_categories(safe: SafePayload) -> dict[str, tuple[str, str]]` LLM fallback for unknowns; (c) `evidence_strength(proposal: CategoryProposal) -> float` per R-6; (d) `order_for_walkthrough(proposals: list[CategoryProposal], deferred: list[str]) -> list[CategoryProposal]` per R-11
- [x] T030 [US1] Implement `bis/slots.py` (depends on T007): `read_slot_state(category: str) -> SlotState | None`, `write_slot_state(state: SlotState) -> Path` (atomic via temp + rename), `append_history(category: str, entry: HistoryEntry) -> None`, `read_bootstrap_run_state() -> BootstrapRunState | None`, `write_bootstrap_run_state(state: BootstrapRunState) -> Path`, `list_existing_slot_categories() -> list[str]`. Append-only history enforced at this layer.
- [x] T031 [US1] Implement `bis/bootstrap.py` orchestration (depends on T025–T030): `detect_existing_state() -> list[str]`, `mine_profile(window: timedelta) -> ProfileSnapshot` (uses github + scanner + cache), `build_proposals(profile: ProfileSnapshot) -> list[CategoryProposal]` (uses categories), `walkthrough_iter(proposals: list[CategoryProposal]) -> Iterator[CategoryProposal]` (applies ordering, surfaces deferred first), `apply_decision(decision: SlotDecision, proposal: CategoryProposal) -> Path | None` (uses slots; returns slot YAML path or None for skip)
- [x] T032 [US1] Implement the `bis init` CLI surface in `bis/cli.py` (depends on T031): `bis init` (interactive, default), `bis init --json --batch`, `bis init confirm --category X --action {accept|change|skip|defer} [--pick name] --json`, flags `--on-existing={merge|replace|skip}`, `--dry-run`, `--print-llm-payloads`, `--no-deep-dive-prompt`. Outputs strictly match the contract schemas (T011–T013 enforce this). Note: `--print-llm-payloads` and `--no-deep-dive-prompt` flags are not yet on the CLI — the skill currently handles deep-dive prompting and no LLM payload print path exists. Tracked as a follow-up; not blocking the MVP.
- [x] T033 [US1] Wire error envelope per `contracts/bootstrap.schema.json` (depends on T032): `gh_auth_missing` when `gh auth status` fails, `no_repos_in_window` when mining returns empty, `existing_state_unresolved` when batch mode lacks `--on-existing`, `scanner_failed` on uncaught parser error. Each error emits `{mode: "error", error: {code, message, hint}}`.

**Checkpoint**: All US1 tests pass. `uv run bis init` against a real `gh auth` session produces slots end-to-end. SC-001 (E2E under 30 min), SC-006 (mining under 5 min for ≤50 repos), SC-009 (cache restart ≤25% cold-run time) are met.

---

## Phase 4: User Story 2 — Deepen each confirmed slot with /deep-dive (Priority: P2)

**Goal**: After each accept/change in the walk-through, the user is offered `/deep-dive` on that slot. Decline keeps the slot persisted but un-dived. A failure in one deep-dive does not block the rest of the walk-through.

**Independent Test**: Run the bootstrap, accept three slots; verify that the deep-dive offer appears after each, that declining still leaves the slot YAML on disk, and that injecting a deep-dive failure on slot #2 still lets slot #3's offer appear.

### Tests for User Story 2

- [~] T034 [P] [US2] Integration test: deep-dive prompt fires once per accept/change, supports `[y/n/all-later/skip-all]` responses; declined slot persists without enrichment in `tests/integration/test_bootstrap_deep_dive_offer.py` — partial: `tests/integration/test_bootstrap_pending_dives.py` covers the CLI side (which slots still need a dive). The conversational `[y/n/all-later/skip-all]` prompt lives in `skills/bis-bootstrap/SKILL.md` and is not unit-tested.
- [x] T035 [P] [US2] Integration test: deep-dive failure on one slot is captured into `deep_dive_failures` in `RunSummary` and does not abort the walk-through (FR-011) in `tests/integration/test_bootstrap_deep_dive_failure.py`

### Implementation for User Story 2

- [x] T036 [US2] Add `bis init pending-dives --json` subcommand to `bis/cli.py` (depends on T032): enumerates confirmed slot categories whose YAML lacks deep-dive enrichment markers, for the skill's batch "all-later" path (R-10)
- [~] T037 [US2] Extend the `RunSummary` event emission in `bis/bootstrap.py` (depends on T031) to include `deep_dive_failures: list[{category, error}]`, populated by the skill via a subsequent `bis init confirm --deep-dive-result ...` flag (or equivalent — design fix during impl) — partial: the `RunSummary` schema accepts `deep_dive_failures`, and the bootstrap pipeline persists run state, but the CLI does not yet emit a `RunSummary` JSON event nor accept `--deep-dive-result`. The skill aggregates failures conversationally. Backfill if/when a non-skill consumer needs it.

**Checkpoint**: US1 + US2 tests both pass. A walk-through end-to-end produces deep-dived slots when the user accepts the offer.

---

## Phase 5: User Story 3 — Run steps 1+2 from a conversational skill (Priority: P3)

**Goal**: A user invokes the bootstrap in Claude Code via a slash command; the skill drives the conversation, calling the CLI in `--json --batch` and `confirm` modes; resulting state is identical to a pure-CLI run.

**Independent Test**: Run `/bis-bootstrap` in Claude Code and a `uv run bis init` in a terminal against the same fixture; assert the resulting `slots/*.yaml` are byte-identical (modulo `decided_at` timestamps).

### Tests for User Story 3

- [x] T038 [P] [US3] Skill ↔ CLI equivalence test: a scripted skill harness (or a transcript-replay test) runs through the same fixture proposals and applies the same decisions as `test_bootstrap_end_to_end.py`; the resulting YAML files must match modulo timestamps. In `tests/integration/test_skill_cli_equivalence.py`

### Implementation for User Story 3

- [x] T039 [US3] Create `skills/bis-bootstrap/SKILL.md` with frontmatter (name, description, trigger `/bis-bootstrap` + natural-language triggers like "bootstrap my slots", "set up my best-in-slot"), and a body that: (a) checks `gh auth status` and `uv` availability, (b) detects existing slots and prompts merge/replace/skip if needed, (c) calls `uv run bis init --json --batch --on-existing=<choice>`, (d) walks the user through each proposal in conversation per `walkthrough-events.schema.json`, (e) calls `uv run bis init confirm ...` per decision, (f) offers `/deep-dive` per accepted/changed slot with the four-way prompt, (g) renders the `RunSummary` at the end
- [x] T040 [US3] Ensure `.claude/skills/` symlink (or whatever the project uses) exposes `skills/bis-bootstrap/`. If the symlink is per-skill, add it; if it's the whole `skills/` dir, no action needed — verify by running `ls .claude/skills/bis-bootstrap/SKILL.md`

**Checkpoint**: All three user stories work independently. The bootstrap skill is discoverable as `/bis-bootstrap` in Claude Code.

---

## Phase 6: User Story 4 — Reshape the slot structure during bootstrap (Priority: P2)

**Why this priority**: US1 fixed the taxonomy as whatever `categories.py` proposes and only let the user choose *within* a slot. Real-world bootstrap usage (commit `3bc2482`) showed the taxonomy itself is often the harder decision — `python-tooling` lumped uv / ruff / ty / pytest / ipykernel into one slot where ipykernel won by frequency, and the user had to hand-edit `bis/categories.py` mid-flight to split it into 5 sub-slots. US4 turns that hand-edit into a first-class conversational affordance: split, merge, rename, drop, add custom slot — presented at two scopes (pre-walk taxonomy review + per-slot inline) so the user reshapes the structure and picks within the (rebuilt) slots in one flow.

**Independent Test**: From a fresh `slots/` dir, the user runs the bootstrap, splits one proposed slot into N sub-slots, merges two proposed slots, renames one slot, drops one slot, adds one custom slot, then walks the rebuilt taxonomy and picks within each — the resulting `slots/*.yaml` set reflects the rebuilt structure and `slots/.bootstrap.yaml` contains a replayable `taxonomy_edits` log.

> **Spec/plan note**: spec.md only documents accept/change/skip/defer (FR-004). T051 backfills US4 + FR-016..FR-020 into spec.md so the contract tests have something to point at. If the user wants the formal Spec Kit flow, run `/speckit-clarify` first against the proposed FRs in T051 before implementing.

### Foundation for User Story 4 (schema + spec extensions)

- [x] T048 [US4] Extend `specs/001-bootstrap-discovery/contracts/walkthrough-events.schema.json` with three new event types — `taxonomy_review_presented` (full proposal-list overview with per-proposal split-suggestion), `structure_action_offered`, `structure_action_applied` — and extend `UserResponse.action` to include `split | merge | rename | drop | add`, each with its auxiliary fields (`into: string[]`, `merge_with: string`, `new_name: string`, `new_category: {name, pick}`)
- [x] T049 [US4] Extend `specs/001-bootstrap-discovery/contracts/bootstrap.schema.json` confirm-branch action enum with `split | merge | rename | drop | add` plus the matching auxiliary fields; ensure existing accept/change/skip/defer outputs still validate (additive change, no removals)
- [x] T050 [P] [US4] Update `specs/001-bootstrap-discovery/data-model.md`: add `StructureChange` entity (discriminated union on `kind: split|merge|rename|drop|add` with per-kind payload), extend `SlotDecision.action` literal, add `BootstrapRunState.taxonomy_edits: list[StructureChange]` (append-only)
- [x] T051 [P] [US4] Append US4 to `specs/001-bootstrap-discovery/spec.md` (mirroring the US1–US3 structure) with FR-016 (structure actions per slot), FR-017 (pre-walk taxonomy review), FR-018 (`taxonomy_edits` audit + replay on resume), FR-019 (structure ops preserve evidence: merge unions, split partitions, rename is identity-on-evidence), FR-020 (split-suggestion is heuristic-driven, not LLM-driven — keeps FR-013 trust boundary intact); add SC-010 (user can reshape ≥1 slot conversationally without editing `categories.py`)

### Tests for User Story 4 (write FIRST, ensure FAIL before T060+)

- [x] T052 [P] [US4] Contract test: `taxonomy_review_presented` and `structure_action_*` events validate against the extended schema; existing event payloads still validate (additive-change regression) in `tests/contract/test_walkthrough_events_structure.py`
- [x] T053 [P] [US4] Contract test: `bis init confirm --action {split|merge|rename|drop|add}` JSON outputs validate against the extended `bootstrap.schema.json` in `tests/contract/test_bootstrap_confirm_structure_output.py`
- [x] T054 [P] [US4] Integration test: end-to-end reshape — fixture proposes `{python-tooling, python-web, databases, docs}`; user issues split(python-tooling → 5 sub-slots), merge(docs into python-web), rename(databases → datastore), drop(one auto-generated sub-slot), add(custom `infra` slot with `terraform`); resulting `slots/*.yaml` set matches expected names + pick assignments in `tests/integration/test_bootstrap_structure_reshape.py`
- [x] T055 [P] [US4] Integration test: pre-walk `taxonomy_review` path — bootstrap emits the full proposal list, user selects "reshape", applies one split, exits review mode, walk-through then iterates the rebuilt taxonomy in FR-014 order in `tests/integration/test_bootstrap_taxonomy_review.py`
- [x] T056 [P] [US4] Integration test: resume after structural edits — user applies split + drop then aborts; next bootstrap run reads `slots/.bootstrap.yaml`, replays `taxonomy_edits` against the fresh proposal set, and re-presents the rebuilt taxonomy without asking the user to redo the structure decisions in `tests/integration/test_bootstrap_structure_resume.py`
- [x] T057 [P] [US4] Unit test: `suggest_split(proposal)` — given a `CategoryProposal` whose members map to ≥2 distinct entries in `CATEGORY_TABLE` (e.g., {uv, ruff, ty, pytest, ipykernel}), returns the partitioned sub-proposals with evidence split per-member; returns `None` when all members share one sub-category in `tests/unit/test_categories_split_suggest.py`
- [x] T058 [P] [US4] Unit test: `merge_proposals(p1, p2, …)` evidence invariant — `repo_count` = sum over disjoint contributing-repo sets (use `set` of repo identities, not naive sum), `most_recent` = `max(…)`, `alternatives` = ordered dedup union, `category_type` must match across inputs (raises `ValueError` on mismatch — caught at CLI layer as `merge_incompatible_types`) in `tests/unit/test_categories_merge.py`
- [x] T059 [P] [US4] Unit test: `apply_rename` and `apply_drop` are pure on `list[CategoryProposal]`, preserve evidence (rename) or remove without leaking into other proposals (drop), and round-trip identically through `replay_taxonomy_edits` in `tests/unit/test_categories_rename_drop.py`

### Implementation for User Story 4

- [x] T060 [P] [US4] Extend `bis/models.py`: add `StructureChange` (Pydantic v2 discriminated union on `kind`), extend `SlotDecision.action` Literal to include the five new variants with optional payload fields (`into`, `merge_with`, `new_name`, `new_category`), add `BootstrapRunState.taxonomy_edits: list[StructureChange] = []`. Validator: structure-change targets must resolve to known category names at apply time (deferred to T062, not at construction time — the run state may reference categories that no longer exist after replay, which is a structural error to surface clearly)
- [x] T061 [P] [US4] Extend `bis/categories.py` with three pure helpers: `suggest_split(proposal: CategoryProposal) -> list[CategoryProposal] | None` (uses `CATEGORY_TABLE` reverse-lookup; returns None when no split possible), `merge_proposals(*proposals: CategoryProposal) -> CategoryProposal` (evidence union per T058), `apply_rename(proposal: CategoryProposal, new_name: str) -> CategoryProposal` (identity on evidence). All deterministic; no LLM calls — keeps FR-013 trust boundary intact (FR-020)
- [x] T062 [US4] Extend `bis/bootstrap.py` (depends on T060, T061): add `apply_structure_change(change: StructureChange, proposals: list[CategoryProposal]) -> list[CategoryProposal]` (pure on the proposal list, dispatches on `kind`), and `replay_taxonomy_edits(proposals: list[CategoryProposal], edits: list[StructureChange]) -> list[CategoryProposal]` for resume. Update `walkthrough_iter` so that after any structure change the iterator re-applies FR-014 ordering against the rebuilt proposal set (do not re-sort during iteration — checkpoint at each structure-change boundary)
- [x] T063 [US4] Extend `bis/slots.py` (depends on T060): `write_bootstrap_run_state` persists `taxonomy_edits` (append-only — never rewrite history), `read_bootstrap_run_state` returns them. Add `append_taxonomy_edit(change: StructureChange) -> None` mirroring the existing `append_history` shape so the invariant is enforced at the storage layer, not the caller
- [x] T064 [US4] Extend `bis/cli.py` (depends on T062, T063): add `bis init taxonomy-review --json` (emits the full proposal-list overview event with `suggest_split` annotations per proposal); extend `bis init confirm` with `--action {split,merge,rename,drop,add}` and aux flags `--into <name1,name2,...>`, `--with <category>`, `--to-name <name>`, `--category <name> --pick <pkg>`. Output strictly matches the extended `bootstrap.schema.json` (T053 enforces)
- [x] T065 [US4] Add `bis init restructure` Typer subcommand to `bis/cli.py` (depends on T064): enters the taxonomy-edit flow against the *last cached proposal set* (read from `slots/.bootstrap.yaml`), without re-mining. Errors with `no_prior_proposal` envelope when run on a fresh project
- [x] T066 [US4] Update `skills/bis-bootstrap/SKILL.md` (depends on T064): (a) insert pre-walk taxonomy-review step that calls `uv run bis init taxonomy-review --json`, renders the full proposal list, asks `[looks good / reshape]`; (b) extend the per-slot prompt with a secondary tier of structural actions presented compactly (`structural: split | merge | rename | drop`) so the primary accept/change/skip/defer prompt stays one-line; (c) "add custom slot" affordance available at any pause; (d) render the structural changes summary (count of splits/merges/renames/drops/adds) in the final `RunSummary` block
- [x] T067 [US4] Wire error envelope additions to `bis/cli.py` per `bootstrap.schema.json` (depends on T064): `unknown_category` (rename/merge/drop target doesn't exist in current proposal set), `split_not_supported` (`suggest_split` returned None and no user-supplied partition provided), `merge_incompatible_types` (e.g., refusing to merge a `language` proposal with a `tooling` proposal — catches the `ValueError` raised in T058), `no_prior_proposal` (T065 entry point with empty `.bootstrap.yaml`). Each emits `{mode: "error", error: {code, message, hint}}`

### US4 docs

- [x] T068 [P] [US4] Update `specs/001-bootstrap-discovery/quickstart.md` with a worked reshape example: bootstrap proposes `python-tooling`, user issues `split` conversationally, walks the 5 resulting sub-slots, ends with the rebuilt structure persisted. Mirror the existing quickstart's prose style.
- [x] T069 [P] [US4] Update root `README.md` to mention slot-structure reshaping (split/merge/rename/drop/add) as a bootstrap capability — one-line addition under the existing "Getting started" block; link to the US4 section of the quickstart.

**Checkpoint**: At this point US4 is independently testable — running `uv run bis init` against any fixture proposal set should let the user reshape the taxonomy conversationally and persist a `slots/*.yaml` set that matches the rebuilt structure, with `slots/.bootstrap.yaml` containing a replayable `taxonomy_edits` log.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T041 [P] Update root `README.md` to add a brief "Getting started" section linking to `specs/001-bootstrap-discovery/quickstart.md`; add a `bis init` row to the slot index introduction
- [x] T042 [P] Run `uv run ty check bis tests` and resolve any type errors (constitution: standalone type hints on all public functions)
- [x] T043 [P] Run `uv run ruff check bis tests && uv run ruff format --check bis tests` and fix
- [x] T044 [P] Add `bis status` Typer subcommand stub in `bis/cli.py` (just prints "TODO" with a pointer to the planned feature) — referenced in `quickstart.md`; full implementation belongs to a future feature
- [ ] T045 Manually walk through `specs/001-bootstrap-discovery/quickstart.md` end-to-end against a real `gh auth` account; record any friction in a follow-up issue — open: needs an interactive `gh auth` session; user has been running parts of the flow in real use (commits `bf6fc74`, `3bc2482`) but the formal quickstart walk-through is not recorded.
- [x] T046 Document the `SCANNER_VERSION` bump procedure as a module docstring in `bis/cache.py` (planning-deferred item: when manifest parser output shape changes, bump the constant; existing cache files are then treated as miss)
- [x] T047 [P] Add `tests/integration/test_bootstrap_low_signal.py` covering the "sparse signal" and "no activity in window" edge cases from spec.md § Edge Cases (already implicitly covered by T017, but worth an explicit assertion that the low-confidence qualifier surfaces)

---

## Phase 8: User Story 5 — Fast hand-off to local walk-through (Priority: P1)

**Why this priority**: Per the 2026-05-22 user feedback ("current bis-bootstrap workflow is way too slow, user spend much time just waiting. If the llm can focus on gathering the historical repo information, then hand off to some cli or questionary type ux, it should speed thing up much faster"). The current bootstrap skill drives a per-slot conversational loop: every accept / change / skip / defer is a separate LLM turn (~5–15s latency × ~12 slots = 2–4 min of waiting that adds no judgment value — the user already knows their preferred pick). US5 redistributes the work along the FR-013 trust boundary: the LLM does the upfront mining + category-inference-on-unknowns (where its judgment is genuinely useful — R-3), then hands off to a local fast TTY walk-through driven by `questionary` (sub-second per-slot decisions), then re-engages once at the end for batched `/deep-dive` chaining. This collapses interactive latency without changing what crosses the trust boundary. P1 because it directly fixes a current-user pain point on the MVP path; without it, every bootstrap session is slow even with US1–US4 complete.

**Independent Test**: Run `/bis-bootstrap` against a fixture proposal set; verify (a) the conversation produces ≤3 LLM turns (mine → handoff → final summary), (b) per-slot decisions happen in a local `questionary` UI driven by keypresses, (c) system-side per-decision latency p95 < 200ms (measured via the deterministic walk adapter), (d) the resulting `slots/*.yaml` set is byte-identical to the prior LLM-in-loop flow (modulo `decided_at` timestamps).

> **Spec/contract drift note**: spec.md currently documents the per-slot conversational flow (FR-010 + the skill in US3). T070 backfills FR-021..FR-024 + SC-011..SC-012 so contract tests have a documented target before implementation lands. If the user wants the formal Spec Kit flow, run `/speckit-clarify` against the proposed FRs in T070 before T072+ tests are written.

### Spec/contract backfill (write FIRST so impl has documented target)

- [x] T070 [US5] Append US5 to `specs/001-bootstrap-discovery/spec.md` (mirroring the US1–US4 structure) with FR-021 (mining-only CLI mode — `bis init mine --json` emits the proposal set + persists it into `slots/.bootstrap.yaml` for handoff, no walk-through), FR-022 (fast local interactive walk-through — `bis init walk` reads the cached proposals and drives a `questionary`-style TTY walk-through with sub-second per-slot system-side latency), FR-023 (the bootstrap skill MUST minimise LLM turns: ≤3 turns per session — mine, handoff, summary; per-slot conversational iteration is forbidden), FR-024 (handoff transport: skill `exec`s `bis init walk` in the user's terminal; resulting slot state is byte-identical to a CLI-only run modulo `decided_at`); add SC-011 (system-side per-slot decision latency p95 < 200ms in the local walk-through) and SC-012 (total LLM-active wall-clock in a bootstrap session < 30s for ≤15 slots, vs the current ≥2 min). Document the trust-boundary invariant: the handoff does not introduce any new payload type; `SafePayload` continues to govern every LLM call in `categories.py` (FR-013 unchanged)

### Setup (extends Phase 1)

- [x] T071 [P] [US5] Add `questionary>=2.0` to `[project.dependencies]` in `pyproject.toml`; run `uv sync` to update `uv.lock`. One-line rationale comment: questionary wraps `prompt_toolkit` to give arrow-key-driven `select`/`checkbox`/`text`/`confirm` — exactly the per-slot affordances the walk-through needs, ≪50ms keypress→render

### Tests for User Story 5 (write FIRST, ensure FAIL before T076+)

- [x] T072 [P] [US5] Integration test: `bis init mine --json` emits the same `proposals` payload shape as `bis init --json --batch` but is decoupled from the walk-through — it writes the proposal set into `slots/.bootstrap.yaml` (a new `pending_proposals` field) and exits without entering any interactive loop. In `tests/integration/test_bootstrap_mine_only.py`. Asserts: exit 0, `mode == "mine"`, `slots/.bootstrap.yaml` exists with `pending_proposals` populated, no `slots/{category}.yaml` files written
- [x] T073 [P] [US5] Integration test: `bis init walk` against a `slots/.bootstrap.yaml` pre-populated with a fixture proposal set drives the questionary walk-through through a deterministic `WalkAdapter` (T075); verifies (a) one `SlotDecision` emitted per proposal, (b) `slots/{category}.yaml` files written for accept/change actions, (c) `pending_proposals` cleared and `deferred_categories`/`taxonomy_edits` updated correctly, (d) final summary JSON matches the existing `RunSummary` shape. In `tests/integration/test_bootstrap_walk_subcommand.py`
- [x] T074 [P] [US5] Integration test: skill-handoff equivalence — drive the new SKILL.md flow (mine via CLI, then `exec bis init walk` with deterministic adapter) against the same fixture proposals as `tests/integration/test_skill_cli_equivalence.py` (T038); resulting `slots/*.yaml` must match the LLM-in-loop output byte-for-byte modulo `decided_at` and `run_id`. In `tests/integration/test_skill_handoff_equivalence.py`. The test fakes the skill side by piping CLI calls; full Claude-Code transcript replay is out of scope (covered by T074's CLI-equivalent invariant)
- [x] T075 [P] [US5] Unit test: `bis/walk.py:WalkAdapter` Protocol — tests inject a scripted answer stream (`["accept", "change:fastapi", "skip", "defer", ...]`), assert one `SlotDecision` is emitted per call, assert the adapter raises on unexpected proposals (no answers left, or extra answers). Assert system-side per-decision latency from `present_proposal` entry to return is < 50ms with the deterministic adapter (no real I/O). In `tests/unit/test_walk_questionary_adapter.py`

### Implementation for User Story 5

- [x] T076 [P] [US5] Create `bis/walk.py` (depends on T060–T065 proposal models): (a) `WalkAdapter` Protocol with `select_action(proposal) -> Literal[...]`, `select_alternative_or_freeform(proposal) -> str`, `confirm_existing_action(category, choices) -> str` — the seam tests use to inject deterministic answers; (b) a `QuestionaryAdapter` concrete impl that uses `questionary.select`/`questionary.text`; (c) a `WalkController` that iterates a `list[CategoryProposal]`, calls the adapter, builds a `SlotDecision`, and yields it; (d) optional progress callback so the CLI's `bis init walk` can print a one-line status per decision without coupling the controller to stdout. Pure on its inputs; no I/O outside the adapter
- [x] T077 [US5] Add `bis init mine` Typer subcommand to `bis/cli.py` (depends on T076 only for the `pending_proposals` schema): runs `mine_profile` + `proposals_for_walkthrough` + `replay_taxonomy_edits` (existing paths) and persists the resulting proposal list into `slots/.bootstrap.yaml` under a new field `pending_proposals: list[CategoryProposal]`. Emits `{mode: "mine", run_id, proposals, skipped_sources, on_existing_choice, taxonomy_edits_replayed: int, pending_proposals_count: int}` to stdout. Does NOT write any `slots/{category}.yaml`. Reuses `start_run_state`/`end_run_state` plumbing
- [x] T078 [US5] Extend `bis/models.py:BootstrapRunState` to add `pending_proposals: list[CategoryProposal] = []` (depends on T077). Update `bis/slots.py:read_bootstrap_run_state`/`write_bootstrap_run_state` to round-trip the field. Append-only invariant does NOT apply to `pending_proposals` (it's overwritten on each `bis init mine` call, cleared on `bis init walk` completion). Update the data-model.md `BootstrapRunState` section to document the new field
- [x] T079 [US5] Add `bis init walk` Typer subcommand to `bis/cli.py` (depends on T076, T077, T078): reads `pending_proposals` from `slots/.bootstrap.yaml` (errors with new `no_pending_proposals` envelope when empty), instantiates `WalkController` + `QuestionaryAdapter`, iterates decisions, calls the existing `apply_decision` for each, clears `pending_proposals` on completion, prints a one-line per-decision summary, and emits a final `{mode: "walk", run_id, decisions_count: {accept, change, skip, defer}, slot_yamls_written: list[str]}`. Flags: `--on-existing={merge,replace}` (forwarded to `apply_decision`), `--from-stdin` (read proposals from stdin as JSON instead of `.bootstrap.yaml` — for the SKILL handoff and for tests)
- [x] T080 [US5] Refactor `bis.cli._interactive_walkthrough` to delegate to `bis/walk.py:WalkController` + `QuestionaryAdapter` instead of the current bare `typer.prompt` loop (depends on T076, T079). The default `bis init` (no flags) continues to run mining → walk-through inline — terminal users get the snappy UX without invoking the skill at all. Preserve the existing dry-run flag behaviour
- [x] T081 [US5] Update `.claude/skills/bis-bootstrap/SKILL.md` (depends on T077, T079): replace the per-slot conversational loop (current Step 2b) with a single "handoff" step. New flow: (Step 1) `gh auth status` + `uv` precheck; (Step 2a) `uv run bis init taxonomy-review --json` for optional pre-walk reshape, same as today; (Step 2b NEW) `uv run bis init mine --json` — emits proposal count + skipped sources, then surface to the user: "Mined N proposals. Hand off to the local walk-through now? (runs `bis init walk` in your terminal — arrow keys + Enter, one keypress per slot.) [y/n]". On `y`, `exec uv run bis init walk` and pause; on `n`, end gracefully (proposals remain in `.bootstrap.yaml` for later); (Step 3 NEW) after the user reports walk completion, read `slots/.bootstrap.yaml` for the summary and call `uv run bis init pending-dives --json` to enumerate confirmed slots, then offer **one** prompt: `Run /deep-dive on all N confirmed slots? [all/none/select]`. SKILL.md MUST NOT iterate proposals conversationally. Add explicit "What this skill MUST NOT do" bullets: don't drive per-slot picks; don't call `bis init confirm` per slot during the walk (the walk-through owns that path now)
- [x] T082 [US5] Add new `no_pending_proposals` and `walk_aborted` error envelopes to `bis/cli.py` + `specs/001-bootstrap-discovery/contracts/bootstrap.schema.json` (depends on T079): `no_pending_proposals` when `bis init walk` runs with no cached proposals (hint: "run `bis init mine` first"); `walk_aborted` when the user `Ctrl-C`s mid-walk (so `pending_proposals` is preserved for a later resume — `bis init walk` is itself idempotent and resumable since it reads from the persisted set)

### US5 polish

- [x] T083 [P] [US5] Add a latency regression test in `tests/integration/test_bootstrap_walk_latency.py`: drives `WalkController` through the deterministic adapter against a 20-proposal fixture; measures wall-clock from `present_proposal` entry to `apply_decision` return per decision; asserts p95 < 200ms (SC-011) and total system-side wall-clock < 4s for the full walk. Skip the test with a clear xfail message on CI if `questionary` import-time alone is the bottleneck (deterministic adapter shouldn't touch questionary, but the import cost is real)
- [x] T084 [P] [US5] Update `specs/001-bootstrap-discovery/quickstart.md` with the new fast-path walk: `bis init mine` → `bis init walk` → `/deep-dive` batch. Mention SC-011/SC-012 explicitly as the user-visible delta vs the prior per-slot conversational loop. Keep the existing single-command `bis init` example as the "everything in one shot for terminal users" path
- [x] T085 [P] [US5] Update root `README.md` "Getting started" block: add one bullet line under the existing `bis init` row — "Fast walk-through: arrow keys + Enter to confirm each slot (powered by questionary)". One line; do not expand the README otherwise
- [x] T086 [P] [US5] Update `bis/cli.py` module docstring + `bis init --help` text to note the new two-step `mine`/`walk` flow as the recommended pattern for skill-driven sessions, with `bis init` (no subcommand) as the recommended one-shot pattern for direct terminal use

**Checkpoint**: A bootstrap session driven from `/bis-bootstrap` completes with ≤3 LLM turns (mine → handoff → summary). Per-slot decisions happen in a local TTY with arrow-key keypresses, system-side latency p95 < 200ms. Resulting `slots/*.yaml` are identical to the prior LLM-in-loop flow. The user's "spend much time just waiting" complaint is resolved against measurable success criteria (SC-011, SC-012).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: no prerequisites
- **Phase 2 (Foundational)**: depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1)**: depends on Phase 2 — the MVP
- **Phase 4 (US2)**: depends on Phase 3 — needs the bootstrap pipeline to add deep-dive plumbing to
- **Phase 5 (US3)**: depends on Phase 3 — needs the CLI surface to wrap; **independent of Phase 4** (skill can offer `/deep-dive` whether or not the `pending-dives` subcommand exists)
- **Phase 6 (US4)**: depends on Phase 3 — extends the bootstrap pipeline + skill; **independent of Phase 4 and Phase 5** (structure actions are orthogonal to deep-dive and to the conversational surface — they apply to whichever entry point the user uses)
- **Phase 7 (Polish)**: depends on whichever stories are shipped
- **Phase 8 (US5)**: depends on Phase 3 (existing CLI surface + walk-through entry point) and Phase 5 (the skill it refactors). **Independent of Phase 6** (US4 structure actions are applied at the proposal level before `bis init mine` persists `pending_proposals`, so the handoff carries an already-reshaped taxonomy through unchanged). T070 (spec backfill) MUST land first; T072–T075 (tests) MUST FAIL before T076+ implementations

### Critical-path ordering inside each phase

- **Within Phase 3 (US1)**: T011–T024 (tests + fixtures) must FAIL before T025–T033 (implementations) land. Within implementation: T029 depends on T027; T030 depends on T007; T031 depends on T025–T030; T032 depends on T031; T033 depends on T032.
- **Within Phase 4 (US2)**: T034–T035 (tests) before T036–T037 (impl). T037 depends on T031.
- **Within Phase 5 (US3)**: T038 (test) before T039 (skill). T040 may be a no-op depending on the existing `.claude/skills/` symlink layout.
- **Within Phase 6 (US4)**: T048–T051 (schema + spec extensions) first — these are the contract. Then T052–T059 (tests, all `[P]`) must FAIL before T060+ implementations land. Within implementation: T060/T061 are independent; T062 depends on T060+T061; T063 depends on T060; T064 depends on T062+T063; T065 depends on T064; T066 depends on T064; T067 depends on T064. T068/T069 (docs) come last but are `[P]` with each other.
- **Within Phase 8 (US5)**: T070 (spec backfill) first — defines FR-021..FR-024 + SC-011..SC-012 the rest hangs off of. T071 (questionary dep) parallel with T070. T072–T075 (tests, all `[P]`) must FAIL before T076+ land. Within implementation: T076 (walk.py) and T078 (model + slots extension for `pending_proposals`) are independent and parallel; T077 (`bis init mine`) depends on T078; T079 (`bis init walk`) depends on T076 + T077 + T078; T080 (refactor `_interactive_walkthrough`) depends on T076 + T079; T081 (SKILL.md rewrite) depends on T077 + T079; T082 (new error envelopes) depends on T079. T083 (latency regression test) depends on T076. T084/T085/T086 (docs) are `[P]` with each other and land last.

### Parallel Opportunities

- **Phase 1**: T003, T004, T005 in parallel after T001/T002.
- **Phase 2**: T007, T008, T010 in parallel; T009 after T007.
- **Phase 3 — tests**: T011–T024 are all `[P]` and can be authored in parallel (different files).
- **Phase 3 — impl**: T025, T026, T027, T028 are all `[P]` (independent modules). T029 and T030 are serial after their deps. T031 → T032 → T033 are serial.
- **Phase 4**: T034 and T035 in parallel.
- **Phase 5**: T039 and T040 effectively serial (T040 is a verification step).
- **Phase 6 — schema/spec**: T050 and T051 in parallel after T048/T049.
- **Phase 6 — tests**: T052–T059 all `[P]` (different files).
- **Phase 6 — impl**: T060 and T061 in parallel; T062/T063 serial after; T064 → {T065, T066, T067} parallel; T068/T069 parallel last.
- **Phase 7**: T041–T044, T047 all `[P]`.
- **Phase 8 — setup**: T070 (spec) and T071 (dep) in parallel.
- **Phase 8 — tests**: T072, T073, T074, T075 all `[P]` (different files).
- **Phase 8 — impl**: T076 and T078 in parallel after tests fail; T077 after T078; T079 after T076+T077+T078; T080/T081/T082 in parallel after T079.
- **Phase 8 — polish**: T083, T084, T085, T086 all `[P]`.

### Parallel example — Phase 3 test wave

```bash
# Author these in parallel (separate files):
Task: "Contract test for --json --batch in tests/contract/test_bootstrap_json_output.py"
Task: "Contract test for confirm in tests/contract/test_bootstrap_confirm_output.py"
Task: "Contract test for walkthrough events in tests/contract/test_walkthrough_events.py"
Task: "Integration test end-to-end in tests/integration/test_bootstrap_end_to_end.py"
Task: "Integration test resume deferred in tests/integration/test_bootstrap_resume_deferred.py"
Task: "Unit test cache TTL in tests/unit/test_cache_ttl.py"
Task: "Unit test categories ordering in tests/unit/test_categories_ordering.py"
Task: "Unit test privacy scrubber in tests/unit/test_privacy_scrubber.py"
Task: "Unit test scanner parsers in tests/unit/test_scanner_parsers.py"
```

```bash
# Then impl wave (independent files):
Task: "Implement bis/scanner.py"
Task: "Implement bis/github.py"
Task: "Implement bis/privacy.py"
Task: "Implement bis/cache.py"
```

### Parallel example — Phase 8 test wave (US5)

```bash
# Author these in parallel (separate files):
Task: "Integration test mine-only in tests/integration/test_bootstrap_mine_only.py"
Task: "Integration test walk subcommand in tests/integration/test_bootstrap_walk_subcommand.py"
Task: "Integration test skill-handoff equivalence in tests/integration/test_skill_handoff_equivalence.py"
Task: "Unit test walk adapter in tests/unit/test_walk_questionary_adapter.py"
```

```bash
# Then impl wave (T076 + T078 are independent; the rest serialise):
Task: "Implement bis/walk.py (WalkAdapter + QuestionaryAdapter + WalkController)"
Task: "Extend bis/models.py BootstrapRunState with pending_proposals"
```

---

## Implementation Strategy

### MVP First (Phases 1 → 2 → 3)

1. Complete Phase 1 (Setup) — toolchain online
2. Complete Phase 2 (Foundational) — models, config, CLI skeleton, test infra
3. Complete Phase 3 (US1) — the full bootstrap pipeline with all tests passing
4. **STOP and VALIDATE**: run `uv run bis init` against a real `gh auth` account; confirm SC-001/002/006 hold; tag the release as MVP

The MVP delivers genuine value: a user can go from zero slots to a confirmed slot set, even without the deep-dive chaining or the conversational skill.

### Incremental Delivery

- After MVP → Phase 4 (deep-dive offer) → ship as a minor version
- After Phase 4 → Phase 5 (skill) → ship as another minor; the skill is the most visible improvement for Claude Code users
- After Phase 5 → Phase 6 (US4 slot-structure UX) → ship as another minor; this is the biggest user-experience improvement after MVP — removes the only known hand-edit (`bis/categories.py` reshape) from the real-world flow
- After Phase 6 → **Phase 8 (US5 fast hand-off)** → ship as another minor; this collapses the per-slot LLM-turn loop into a single local walk-through, removing the 2–4 min of latency the user spends "just waiting" per session. P1 priority because it materially affects the existing MVP UX — every shipped bootstrap session benefits immediately
- Phase 7 (polish) folds in alongside whichever stories ship

### Parallel team strategy

- One developer can carry the whole stack through MVP in ~2–3 focused days
- With two: split the Phase 3 implementation cluster (scanner+github+privacy+cache vs categories+slots+bootstrap+cli)
- US2, US3, and US4 can be picked up by different developers in parallel once US1 lands — all three extend the bootstrap pipeline along orthogonal axes (enrichment, surface, structure)

---

## Notes

- Test-first within each user story is non-negotiable for the implementation tasks — write the failing test, then make it pass.
- File paths are absolute relative to repo root. `[P]` markers are accurate as of generation; if a refactor introduces a cross-task file dependency, drop the `[P]`.
- The deferred TODO from R-12 ("pixi configs still on 3.12.*") is intentionally out of scope here — it's slot content, not bootstrap-feature scope.
- Privacy is the single biggest correctness risk: T022 is the canary. Reviewers should `grep -r 'to_safe_payload\|SafePayload' bis/` on any PR touching `categories.py` or any future LLM call site.
- US4 (Phase 6) extends `bis/categories.py` with split/merge helpers — these MUST stay deterministic (FR-020). Reviewers: ensure `suggest_split` reads only `CATEGORY_TABLE`, never the LLM-fallback path. The privacy invariant from T022 holds because US4 does not introduce any new payload type — the existing `SafePayload` scrubber covers it.
- US4 spec drift: spec.md currently documents only accept/change/skip/defer (FR-004). T051 backfills FR-016..FR-020 before any code lands so contract tests have a documented target. Consider running `/speckit-clarify` against those FRs before T052–T059 are written if there's any uncertainty about exact wording — clarifying after tests land creates churn.
- US5 spec drift: spec.md + the existing skill describe a per-slot conversational walk-through (FR-010 + Step 2b of `skills/bis-bootstrap/SKILL.md`). T070 backfills FR-021..FR-024 + SC-011..SC-012 before T076+ land. Same precedent as US4 — consider `/speckit-clarify` against the proposed FRs first if the wording (especially the SC-011 latency budget and SC-012 LLM-turn cap) needs sharpening.
- US5 trust-boundary invariant: the hand-off does NOT introduce any new payload type. The LLM still calls `categories.infer_categories` with a `SafePayload` during `bis init mine`; nothing else crosses the boundary. The walk-through is fully local. Reviewers: re-run the `grep -r 'to_safe_payload\|SafePayload' bis/` invariant after T076–T082 land.
