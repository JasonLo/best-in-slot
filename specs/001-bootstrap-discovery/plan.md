# Implementation Plan: Bootstrap Discovery Pipeline

**Branch**: `001-bootstrap-discovery` | **Date**: 2026-05-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-bootstrap-discovery/spec.md`

## Summary

Bootstrap discovery is a four-step pipeline that takes a user from "no slots" to "a confirmed, evidence-anchored slot set":

1. **Mine** — scan repos the user has touched in the last 3 years (public + private + member orgs) via `gh`, parse manifests, and aggregate into per-tool signals. Per-repo results are cached for ~24h (FR-015).
2. **Propose** — translate tool signals into draft `CategoryProposal`s with `language | framework | tooling` typing and evidence (FR-003/FR-014).
3. **Walk-through** — present proposals one slot at a time, grouped languages → frameworks → tooling, evidence-strength within group. User picks accept / change (observed or free-form) / skip / defer (FR-004/FR-014, Q1, Q4).
4. **Persist + deepen** — write `slots/{category}.yaml` state for each confirmed slot; offer `/deep-dive` per slot (FR-005/FR-006).

This plan also scaffolds the `bis` Python CLI itself: the current `bis/` directory only has stale `.pyc` files (no committed source) and there is no `pyproject.toml`. The bootstrap feature therefore brings up the toolchain (uv + Typer + Pydantic v2 + httpx + PyYAML) and the foundational modules referenced by the constitution (`models.py`, `slots.py`, `scanner.py`, `github.py`, `cli.py`, `config.py`) alongside the bootstrap-specific code.

## Technical Context

**Language/Version**: Python 3.14+ (pin `requires-python = ">=3.14"` in `pyproject.toml`). Matches the constitution v1.1.0 floor and the README's single-floor 3.14 declaration.

**Primary Dependencies**: Typer (CLI), Pydantic v2 (boundary models), httpx (registry calls — used by future features, not bootstrap), PyYAML (slot/cache persistence), `tomli` / stdlib `tomllib` (manifest parsing), `gh` CLI as subprocess (constitution Principle V).

**Storage**: YAML on disk only. Slot state in `slots/{category}.yaml`. Per-repo mining cache in `.bis/cache/repos/{owner}/{repo}.yaml`. Bootstrap-run state (deferred slots, skipped sources) in `slots/.bootstrap.yaml`. No databases, no key-value stores (constitution Principle II).

**Testing**: pytest + pytest-asyncio. Three tiers: `tests/contract/` (CLI JSON output schema validation), `tests/integration/` (end-to-end bootstrap with a `gh` stub binary and fixture repos), `tests/unit/` (cache TTL, ordering, category inference, privacy scrubber).

**Target Platform**: macOS / Linux developer machines with a working `gh` CLI session. WSL2 supported.

**Project Type**: Single-project Python CLI (no frontend, no backend service, no mobile).

**Performance Goals**: SC-006 — mining wall-clock under 5 min for ≤50 repos in the 3y window. SC-001 — full E2E (mine → propose → confirm → deep-dive) under 30 min for the same scale. SC-009 — cached restart completes mining in ≤25% of cold-run time.

**Constraints**:
- FR-013 — only package names + frequencies + recency timestamps may cross a trust boundary (e.g., to an LLM). Raw manifest bodies, READMEs, source files MUST stay local. Enforced by routing every LLM-bound payload through `bis/privacy.py`.
- FR-015 — per-repo cache TTL ≈ 24h; older entries refresh on next scan.
- Constitution: no background daemons, no servers, no PyGithub, no direct `GITHUB_TOKEN` reads.

**Scale/Scope**: Designed for an individual user's GitHub presence — typically 10–500 repos in the trailing 3-year window. Mining must remain bounded by `gh` rate limits (handled transparently by `gh`); no hard cap beyond what `gh` enforces.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance | Evidence |
|---|---|---|
| **I. Python does data, Claude does judgment** | PASS | All scanning, parsing, aggregation, scoring, ordering, and YAML I/O lives in `bis/`. The conversational confirmation walk-through is driven by the skill layer (`skills/bis-bootstrap/SKILL.md`) — the CLI offers a `--json` and `--batch` mode the skill orchestrates. Category inference defaults to deterministic heuristics; LLM is consulted only on unknowns and only with the scrubbed `SafePayload`. |
| **II. YAML is the source of truth** | PASS | Slot state: `slots/{category}.yaml`. Run state: `slots/.bootstrap.yaml`. Mining cache: `.bis/cache/repos/{owner}/{repo}.yaml`. No SQLite, no Postgres, no JSON-blob store. |
| **III. Skills wrap the CLI** | PASS | `bis bootstrap` is a Typer subcommand. The bootstrap skill (User Story 3) shells out via `uv run bis bootstrap` and adds conversational framing — it does not re-parse manifests or hit `gh` directly. |
| **IV. Modern Python toolchain** | PASS | uv-managed env, Typer for CLI, Pydantic v2 for every boundary model in `bis/models.py`, httpx for any HTTP (none in bootstrap itself; reserved for registry calls). |
| **V. `gh` for GitHub** | PASS | All repo listing, manifest fetching, and org membership lookups go through `gh api ...` invoked from `bis/github.py`. No `GITHUB_TOKEN` read, no PyGithub. |

**Constitutional concern flagged**: The constitution's "Skill / CLI Workflow" section says *"Every user-facing capability MUST have BOTH a `bis` subcommand and a SKILL.md."* The bootstrap skill is marked P3 (nice-to-have) in the spec but is required by this gate. **Resolution**: include the SKILL.md in the P1 implementation scope but keep its surface minimal (slash command that runs the CLI in `--json --batch` mode and renders results). This satisfies the constitution without expanding the spec.

**All gates pass.**

## Project Structure

### Documentation (this feature)

```text
specs/001-bootstrap-discovery/
├── plan.md                       # This file
├── spec.md                       # Already exists
├── research.md                   # Phase 0 output
├── data-model.md                 # Phase 1 output
├── quickstart.md                 # Phase 1 output
├── contracts/                    # Phase 1 output
│   ├── bootstrap.schema.json
│   └── walkthrough-events.schema.json
├── checklists/
│   └── requirements.md           # From /speckit-specify
└── tasks.md                      # NOT created here — /speckit-tasks job
```

### Source Code (repository root)

```text
bis/                              # Python package — scaffolded by this feature
├── __init__.py
├── cli.py                        # Typer app: `bis bootstrap`, `bis status`, …
├── models.py                     # Pydantic v2: RepoRef, ToolSignal, CategoryProposal,
│                                 #   SlotDecision, SlotState, BootstrapRunState, SafePayload
├── slots.py                      # YAML CRUD for slots/{category}.yaml + slots/.bootstrap.yaml
├── scanner.py                    # Manifest parsers (pyproject.toml, package.json, go.mod,
│                                 #   Cargo.toml, Gemfile, requirements.txt)
├── github.py                     # gh subprocess wrappers (list_repos, get_manifest, list_orgs)
├── cache.py                      # Per-repo scan cache, ~24h TTL (FR-015)
├── categories.py                 # Category inference + language/framework/tooling tagging
│                                 #   and evidence-strength scoring for ordering (FR-014)
├── bootstrap.py                  # Pipeline orchestration: detect-existing → mine → propose
│                                 #   → walkthrough → persist (FR-001..FR-012)
├── privacy.py                    # SafePayload builder; trust-boundary scrubber (FR-013)
└── config.py                     # settings.yaml loader

skills/
└── bis-bootstrap/
    └── SKILL.md                  # P3 / constitution-mandated wrapper (User Story 3)

slots/
├── {category}.yaml               # NEW: slot state index (produced by bootstrap)
├── .bootstrap.yaml               # NEW: bootstrap-run state (deferred slots, skipped sources)
└── {category}/{tool}/            # PRESERVED: existing human-curated README/CHEATSHEET content

tests/
├── contract/
│   ├── test_bootstrap_json_output.py
│   └── test_walkthrough_events.py
├── integration/
│   ├── test_bootstrap_end_to_end.py     # with gh stub + fixture repos
│   ├── test_bootstrap_resume_deferred.py
│   ├── test_bootstrap_cache_hit.py
│   └── test_bootstrap_partial_access.py # private/org access denied
└── unit/
    ├── test_cache_ttl.py
    ├── test_categories_ordering.py       # FR-014 grouping + tiebreak
    ├── test_categories_inference.py
    ├── test_privacy_scrubber.py          # FR-013 no-leak assertion
    └── test_scanner_parsers.py

pyproject.toml                    # NEW: uv-managed; pins toolchain
.bis/                             # NEW: local cache root (gitignored)
└── cache/repos/{owner}/{repo}.yaml
.gitignore                        # UPDATE: add .bis/, profile.yaml
```

**Structure Decision**: Single-project Python CLI laid out under `bis/`. The directory exists already (with stale `.pyc` only — no committed source). The bootstrap feature scaffolds the toolchain (`pyproject.toml`, uv lock) and implements every module listed above. Slot content under `slots/{category}/{tool}/` is preserved as-is; bootstrap adds a sibling state file `slots/{category}.yaml` and a single hidden `slots/.bootstrap.yaml` for run state. Tests live at repo root following the pytest convention already implied by the constitution.

## Complexity Tracking

| Item | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Dedicated `bis/privacy.py` module | FR-013 requires that no raw repo content leaves the machine, ever. Centralising the scrubber lets the no-leak invariant be unit-tested and lets reviewers grep for any LLM call that bypasses it. | Inline scrubbing at each call site: invariant becomes a discipline rather than a check; one missed call site silently exfiltrates data. |
| `slots/.bootstrap.yaml` sidecar (instead of per-slot deferred fields) | Resume of deferred slots (FR-012, SC-007) is a *run-level* concept, not a per-slot one — the list of deferred slots IS the run's resume pointer. Putting it in each slot YAML would force readers to iterate every slot to find what is pending. | Per-slot `status: deferred` field: works but spreads the resume state across N files, making the next-run query an O(N) scan instead of one file read. |
| Per-repo cache file granularity (not one big cache file) | Concurrent writes during scan, partial invalidation on TTL miss, and easy manual inspection ("why did this repo not get rescanned?") all favour one file per repo. | Single `cache.yaml`: simpler to read but locks under concurrency, harder to invalidate per entry, harder to diff. |

No constitution violations to justify.
