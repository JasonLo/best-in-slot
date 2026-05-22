<!--
Sync Impact Report
==================
Version change: (template) → 1.0.0
Bump rationale: Initial ratification of the Best-in-Slot constitution.

Principles defined (all new):
  I.   Python does Data, Claude does Judgment
  II.  YAML is the Source of Truth (no databases)
  III. Skills Wrap the CLI (not the other way around)
  IV.  Modern Python Toolchain (uv · Typer · Pydantic v2 · httpx)
  V.   Lean on `gh` for GitHub (no raw token management)

Added sections:
  - Tech Stack Constraints
  - Skill / CLI Workflow
  - Governance

Removed sections: none.

Templates requiring updates:
  - .specify/templates/plan-template.md     ✅ Constitution Check gate will resolve against these principles (no edits required; placeholder block is generic).
  - .specify/templates/spec-template.md     ✅ No scope/constraint additions imposed by this constitution that are not already general.
  - .specify/templates/tasks-template.md    ✅ Task categories unchanged; principles inform review, not task taxonomy.
  - .specify/templates/checklist-template.md ✅ Compatible as-is.
  - README.md                                ⚠ Consider linking to .specify/memory/constitution.md from the README "Architecture" section (not blocking).

Deferred TODOs: none.
-->

# Best-in-Slot Constitution

## Core Principles

### I. Python does Data, Claude does Judgment
Deterministic work — fetching repos, parsing dependency files, computing scores,
reading/writing YAML — MUST live in Python under `bis/`. Qualitative work —
weighing trade-offs, comparing APIs, writing recommendations, deciding when to
switch tools — MUST live in skills under `skills/`. A Python module MUST NOT
contain rhetoric about *whether* a tool is good; it computes signals only. A
skill MUST NOT re-implement what a `bis` command already does; it calls the
command and reasons over the output.
**Rationale:** Keeps deterministic logic testable and reproducible while letting
the LLM do what only it can do well — context-sensitive judgment.

### II. YAML is the Source of Truth (no databases)
All persistent project state — slot picks, alternatives, profile, settings,
switch history — MUST be stored as YAML on disk. No SQLite, no Postgres, no
JSON blobs in a key-value store. Slot files MUST be named `{category}.yaml` and
live under `slots/`. All CRUD MUST go through `bis/slots.py`.
**Rationale:** YAML is diffable, reviewable in PRs, git-native, and human-
editable in an emergency. The project's value is the *content* of these files,
not the storage layer.

### III. Skills Wrap the CLI (not the other way around)
Every category-level operation (evaluate, discover, switch, status, show) MUST
exist as a `bis` subcommand that returns structured data (JSON or YAML). Skills
MUST invoke that subcommand via `uv run bis ...`, then add qualitative
reasoning on top. CLI subcommands MUST NOT shell out to Claude. Skills MUST NOT
parse dependency files or hit registries directly.
**Rationale:** The CLI is callable by anyone (CI, scripts, other agents); the
skill layer is callable only inside Claude. Inverting the dependency would
trap the deterministic work inside the agent.

### IV. Modern Python Toolchain (uv · Typer · Pydantic v2 · httpx)
The toolchain is fixed and non-negotiable for new code:
- Dependency & env management: **uv** (no pip, no Poetry, no conda).
- CLI framework: **Typer** (no Click, no argparse).
- Data models: **Pydantic v2** for everything that crosses a boundary (YAML,
  HTTP, CLI args). No dataclasses for the same role.
- HTTP: **httpx** (no `requests`, no `urllib`).
- All persistent data: YAML (see Principle II).

Changing any of these is a MAJOR constitution amendment.
**Rationale:** Consistency lowers cognitive load. Each choice is also the
current best-in-class for its slot — eating our own dog food.

### V. Lean on `gh` for GitHub (no raw token management)
All GitHub API access MUST go through `gh api` invoked as a subprocess. The
project MUST NOT read `GITHUB_TOKEN` directly, MUST NOT store tokens in YAML
or env files it owns, and MUST NOT use a Python GitHub SDK (`PyGithub`, etc.).
Auth is delegated to `gh auth`.
**Rationale:** Avoids an entire category of secret-handling bugs. Users
already have `gh` configured; we get free auth, rate-limit handling, and
enterprise/SSO support.

## Tech Stack Constraints

- **Language/Version:** Python ≥ 3.11. No Python 2, no untyped code paths in
  `bis/`.
- **Type checking:** Pydantic models for I/O boundaries; standalone type hints
  on all public functions in `bis/`.
- **Scoring dimensions are versioned:** Weights (personal usage 0.30,
  community 0.25, maintenance 0.20, ecosystem 0.15, migration 0.10) live in
  code and are part of the public contract. Changing a weight is a MINOR
  amendment; adding/removing a dimension is MAJOR.
- **No background daemons / no servers.** BIS is a CLI plus a set of YAML
  files. If a feature appears to require a long-running process, that is a
  signal to redesign, not a signal to add infrastructure.
- **External calls are cached or rate-limit-aware.** Registry calls (PyPI,
  npm) and GitHub calls MUST tolerate the absence of network (degrade
  gracefully to "unknown" rather than crash).

## Skill / CLI Workflow

- Every user-facing capability MUST have BOTH a `bis` subcommand (machine-
  callable, structured output) and a SKILL.md (Claude-callable, prose
  reasoning). Adding one without the other is a Constitution Check failure.
- SKILL.md files MUST be authored under `skills/<name>/SKILL.md` and exposed
  via the `.claude/skills` symlink. They MUST NOT duplicate logic from
  `bis/`.
- Dependency parsers in `bis/scanner.py` MUST return `dict[str, list[str]]`
  of normalised package names. Normalisation rules MUST be uniform across
  languages (lowercase, dashes-not-underscores for Python, scoped names
  preserved for npm).
- Switch history is append-only. `bis switch` MUST record `from`, `to`,
  `reason`, and `date` in the slot file. Editing past history entries is
  forbidden outside of a documented migration.

## Governance

- This constitution supersedes ad-hoc decisions, READMEs, and prior chat
  context. Where they conflict, the constitution wins.
- Amendments require a PR that updates `.specify/memory/constitution.md` and
  any dependent templates flagged in the Sync Impact Report. The PR
  description MUST state the version bump and rationale.
- Versioning policy (semantic versioning of this document):
  - **MAJOR:** Principle removed, redefined incompatibly, or toolchain
    swapped (e.g., dropping Typer).
  - **MINOR:** New principle, new mandatory section, or materially expanded
    guidance.
  - **PATCH:** Wording, typo, clarification with no behavioural change.
- Compliance review: Every PR that adds a `bis` subcommand, a skill, a slot
  category, or a scoring dimension MUST be checked against Principles I–V
  before merge. The Constitution Check gate in `plan-template.md` enforces
  this for spec-kit-driven features.
- Complexity must be justified. If a feature appears to require violating a
  principle, the PR MUST include a "Complexity Justification" section
  explaining why no compliant design exists. Reviewers SHOULD push back on
  unjustified violations.

**Version**: 1.0.0 | **Ratified**: 2026-05-22 | **Last Amended**: 2026-05-22
