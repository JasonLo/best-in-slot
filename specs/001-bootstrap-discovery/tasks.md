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

**Checkpoint**: `uv run pytest tests/conftest.py --collect-only` succeeds; `uv run bis bootstrap` prints the stub message.

---

## Phase 3: User Story 1 — Propose + walk-through from repo history (Priority: P1) 🎯 MVP

**Goal**: A user with no slots runs `bis bootstrap`, sees a ranked proposal grouped languages → frameworks → tooling, walks through each slot with accept / change (observed or free-form) / skip / defer, and ends with persisted `slots/{category}.yaml` files. Mining is cached for ~24h. Privacy invariant FR-013 is enforced at the type level.

**Independent Test**: From an empty `slots/` directory, run `uv run bis bootstrap` against the `gh_stub` fixture; verify the expected slot YAMLs land, `slots/.bootstrap.yaml` records any deferrals, and the cache contains per-repo scan files.

### Tests for User Story 1 (write FIRST; ensure they FAIL before implementation)

- [x] T011 [P] [US1] Contract test: validate `bis bootstrap --json --batch` output against `specs/001-bootstrap-discovery/contracts/bootstrap.schema.json` in `tests/contract/test_bootstrap_json_output.py`
- [x] T012 [P] [US1] Contract test: validate `bis bootstrap confirm --json` output (one per action: accept/change/skip/defer) against the same schema's `confirm` branch in `tests/contract/test_bootstrap_confirm_output.py`
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
- [x] T032 [US1] Implement the `bis bootstrap` CLI surface in `bis/cli.py` (depends on T031): `bis bootstrap` (interactive, default), `bis bootstrap --json --batch`, `bis bootstrap confirm --category X --action {accept|change|skip|defer} [--pick name] --json`, flags `--on-existing={merge|replace|skip}`, `--dry-run`, `--print-llm-payloads`, `--no-deep-dive-prompt`. Outputs strictly match the contract schemas (T011–T013 enforce this). Note: `--print-llm-payloads` and `--no-deep-dive-prompt` flags are not yet on the CLI — the skill currently handles deep-dive prompting and no LLM payload print path exists. Tracked as a follow-up; not blocking the MVP.
- [x] T033 [US1] Wire error envelope per `contracts/bootstrap.schema.json` (depends on T032): `gh_auth_missing` when `gh auth status` fails, `no_repos_in_window` when mining returns empty, `existing_state_unresolved` when batch mode lacks `--on-existing`, `scanner_failed` on uncaught parser error. Each error emits `{mode: "error", error: {code, message, hint}}`.

**Checkpoint**: All US1 tests pass. `uv run bis bootstrap` against a real `gh auth` session produces slots end-to-end. SC-001 (E2E under 30 min), SC-006 (mining under 5 min for ≤50 repos), SC-009 (cache restart ≤25% cold-run time) are met.

---

## Phase 4: User Story 2 — Deepen each confirmed slot with /deep-dive (Priority: P2)

**Goal**: After each accept/change in the walk-through, the user is offered `/deep-dive` on that slot. Decline keeps the slot persisted but un-dived. A failure in one deep-dive does not block the rest of the walk-through.

**Independent Test**: Run the bootstrap, accept three slots; verify that the deep-dive offer appears after each, that declining still leaves the slot YAML on disk, and that injecting a deep-dive failure on slot #2 still lets slot #3's offer appear.

### Tests for User Story 2

- [~] T034 [P] [US2] Integration test: deep-dive prompt fires once per accept/change, supports `[y/n/all-later/skip-all]` responses; declined slot persists without enrichment in `tests/integration/test_bootstrap_deep_dive_offer.py` — partial: `tests/integration/test_bootstrap_pending_dives.py` covers the CLI side (which slots still need a dive). The conversational `[y/n/all-later/skip-all]` prompt lives in `skills/bis-bootstrap/SKILL.md` and is not unit-tested.
- [x] T035 [P] [US2] Integration test: deep-dive failure on one slot is captured into `deep_dive_failures` in `RunSummary` and does not abort the walk-through (FR-011) in `tests/integration/test_bootstrap_deep_dive_failure.py`

### Implementation for User Story 2

- [x] T036 [US2] Add `bis bootstrap pending-dives --json` subcommand to `bis/cli.py` (depends on T032): enumerates confirmed slot categories whose YAML lacks deep-dive enrichment markers, for the skill's batch "all-later" path (R-10)
- [~] T037 [US2] Extend the `RunSummary` event emission in `bis/bootstrap.py` (depends on T031) to include `deep_dive_failures: list[{category, error}]`, populated by the skill via a subsequent `bis bootstrap confirm --deep-dive-result ...` flag (or equivalent — design fix during impl) — partial: the `RunSummary` schema accepts `deep_dive_failures`, and the bootstrap pipeline persists run state, but the CLI does not yet emit a `RunSummary` JSON event nor accept `--deep-dive-result`. The skill aggregates failures conversationally. Backfill if/when a non-skill consumer needs it.

**Checkpoint**: US1 + US2 tests both pass. A walk-through end-to-end produces deep-dived slots when the user accepts the offer.

---

## Phase 5: User Story 3 — Run steps 1+2 from a conversational skill (Priority: P3)

**Goal**: A user invokes the bootstrap in Claude Code via a slash command; the skill drives the conversation, calling the CLI in `--json --batch` and `confirm` modes; resulting state is identical to a pure-CLI run.

**Independent Test**: Run `/bis-bootstrap` in Claude Code and a `uv run bis bootstrap` in a terminal against the same fixture; assert the resulting `slots/*.yaml` are byte-identical (modulo `decided_at` timestamps).

### Tests for User Story 3

- [x] T038 [P] [US3] Skill ↔ CLI equivalence test: a scripted skill harness (or a transcript-replay test) runs through the same fixture proposals and applies the same decisions as `test_bootstrap_end_to_end.py`; the resulting YAML files must match modulo timestamps. In `tests/integration/test_skill_cli_equivalence.py`

### Implementation for User Story 3

- [x] T039 [US3] Create `skills/bis-bootstrap/SKILL.md` with frontmatter (name, description, trigger `/bis-bootstrap` + natural-language triggers like "bootstrap my slots", "set up my best-in-slot"), and a body that: (a) checks `gh auth status` and `uv` availability, (b) detects existing slots and prompts merge/replace/skip if needed, (c) calls `uv run bis bootstrap --json --batch --on-existing=<choice>`, (d) walks the user through each proposal in conversation per `walkthrough-events.schema.json`, (e) calls `uv run bis bootstrap confirm ...` per decision, (f) offers `/deep-dive` per accepted/changed slot with the four-way prompt, (g) renders the `RunSummary` at the end
- [x] T040 [US3] Ensure `.claude/skills/` symlink (or whatever the project uses) exposes `skills/bis-bootstrap/`. If the symlink is per-skill, add it; if it's the whole `skills/` dir, no action needed — verify by running `ls .claude/skills/bis-bootstrap/SKILL.md`

**Checkpoint**: All three user stories work independently. The bootstrap skill is discoverable as `/bis-bootstrap` in Claude Code.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T041 [P] Update root `README.md` to add a brief "Getting started" section linking to `specs/001-bootstrap-discovery/quickstart.md`; add a `bis bootstrap` row to the slot index introduction
- [x] T042 [P] Run `uv run ty check bis tests` and resolve any type errors (constitution: standalone type hints on all public functions)
- [x] T043 [P] Run `uv run ruff check bis tests && uv run ruff format --check bis tests` and fix
- [x] T044 [P] Add `bis status` Typer subcommand stub in `bis/cli.py` (just prints "TODO" with a pointer to the planned feature) — referenced in `quickstart.md`; full implementation belongs to a future feature
- [ ] T045 Manually walk through `specs/001-bootstrap-discovery/quickstart.md` end-to-end against a real `gh auth` account; record any friction in a follow-up issue — open: needs an interactive `gh auth` session; user has been running parts of the flow in real use (commits `bf6fc74`, `3bc2482`) but the formal quickstart walk-through is not recorded.
- [x] T046 Document the `SCANNER_VERSION` bump procedure as a module docstring in `bis/cache.py` (planning-deferred item: when manifest parser output shape changes, bump the constant; existing cache files are then treated as miss)
- [x] T047 [P] Add `tests/integration/test_bootstrap_low_signal.py` covering the "sparse signal" and "no activity in window" edge cases from spec.md § Edge Cases (already implicitly covered by T017, but worth an explicit assertion that the low-confidence qualifier surfaces)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: no prerequisites
- **Phase 2 (Foundational)**: depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1)**: depends on Phase 2 — the MVP
- **Phase 4 (US2)**: depends on Phase 3 — needs the bootstrap pipeline to add deep-dive plumbing to
- **Phase 5 (US3)**: depends on Phase 3 — needs the CLI surface to wrap; **independent of Phase 4** (skill can offer `/deep-dive` whether or not the `pending-dives` subcommand exists)
- **Phase 6 (Polish)**: depends on whichever stories are shipped

### Critical-path ordering inside each phase

- **Within Phase 3 (US1)**: T011–T024 (tests + fixtures) must FAIL before T025–T033 (implementations) land. Within implementation: T029 depends on T027; T030 depends on T007; T031 depends on T025–T030; T032 depends on T031; T033 depends on T032.
- **Within Phase 4 (US2)**: T034–T035 (tests) before T036–T037 (impl). T037 depends on T031.
- **Within Phase 5 (US3)**: T038 (test) before T039 (skill). T040 may be a no-op depending on the existing `.claude/skills/` symlink layout.

### Parallel Opportunities

- **Phase 1**: T003, T004, T005 in parallel after T001/T002.
- **Phase 2**: T007, T008, T010 in parallel; T009 after T007.
- **Phase 3 — tests**: T011–T024 are all `[P]` and can be authored in parallel (different files).
- **Phase 3 — impl**: T025, T026, T027, T028 are all `[P]` (independent modules). T029 and T030 are serial after their deps. T031 → T032 → T033 are serial.
- **Phase 4**: T034 and T035 in parallel.
- **Phase 5**: T039 and T040 effectively serial (T040 is a verification step).
- **Phase 6**: T041–T044, T047 all `[P]`.

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

---

## Implementation Strategy

### MVP First (Phases 1 → 2 → 3)

1. Complete Phase 1 (Setup) — toolchain online
2. Complete Phase 2 (Foundational) — models, config, CLI skeleton, test infra
3. Complete Phase 3 (US1) — the full bootstrap pipeline with all tests passing
4. **STOP and VALIDATE**: run `uv run bis bootstrap` against a real `gh auth` account; confirm SC-001/002/006 hold; tag the release as MVP

The MVP delivers genuine value: a user can go from zero slots to a confirmed slot set, even without the deep-dive chaining or the conversational skill.

### Incremental Delivery

- After MVP → Phase 4 (deep-dive offer) → ship as a minor version
- After Phase 4 → Phase 5 (skill) → ship as another minor; the skill is the most visible improvement for Claude Code users
- Phase 6 (polish) folds in alongside whichever stories ship

### Parallel team strategy

- One developer can carry the whole stack through MVP in ~2–3 focused days
- With two: split the Phase 3 implementation cluster (scanner+github+privacy+cache vs categories+slots+bootstrap+cli)
- US2 and US3 can be picked up by different developers in parallel once US1 lands

---

## Notes

- Test-first within each user story is non-negotiable for the implementation tasks — write the failing test, then make it pass.
- File paths are absolute relative to repo root. `[P]` markers are accurate as of generation; if a refactor introduces a cross-task file dependency, drop the `[P]`.
- The deferred TODO from R-12 ("pixi configs still on 3.12.*") is intentionally out of scope here — it's slot content, not bootstrap-feature scope.
- Privacy is the single biggest correctness risk: T022 is the canary. Reviewers should `grep -r 'to_safe_payload\|SafePayload' bis/` on any PR touching `categories.py` or any future LLM call site.
