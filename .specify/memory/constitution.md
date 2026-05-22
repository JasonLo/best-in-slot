<!--
Sync Impact Report
==================
Version change: 1.1.0 → 1.2.0
Bump rationale: Add three new product-purpose principles (VI–VIII) that
codify what BIS is *for*, complementing the existing five principles
(I–V) that codify *how* it is built. MINOR per the governance policy —
"new principle/section added or materially expanded guidance". No
existing principle is removed, redefined, or relaxed.

Principles added:
  - VI. Mine the User's History, Don't Ask for It
        Slot defaults MUST be derived from the user's profile (frequency
        × recency across user + org repos). Manual / fallback picks MUST
        be marked with `source:` and surfaced. Asking the user to declare
        their stack from scratch is a failure mode.
  - VII. Surface New Winners, Not Just Catalogue Old Ones
        `bis discover` MUST proactively flag candidates that score
        meaningfully higher than the current pick on dimensions overlapping
        the user's profile signal, and the skill layer MUST emit a short
        TL;DR (current pick → candidate, the 2–3 signals that flipped,
        suggested action). Stale-slot detection runs on every `bis status`.
  - VIII. Flag Outdated In-Package Usage
        Beyond cross-package swaps, BIS MUST detect outdated *intra*-
        package patterns (deprecated APIs, pre-major-version idioms) in
        packages the user still depends on, record them under an
        `outdated_patterns:` key on the relevant slot with a citation to
        the modern equivalent, and surface them via `bis status` / a
        dedicated subcommand.

Principles changed: none (no removal, no incompatible redefinition).

Sections modified:
  - Governance → Compliance review now also checks PRs that add an
    outdated-pattern detector or a profile-derivation signal.

Templates requiring updates:
  - .specify/templates/plan-template.md      ✅ No edits; the Constitution
    Check gate references the constitution generically ("Gates determined
    based on constitution file"), so the new principles are picked up
    automatically.
  - .specify/templates/spec-template.md      ✅ Compatible as-is.
  - .specify/templates/tasks-template.md     ✅ Compatible as-is.
  - .specify/templates/checklist-template.md ✅ Compatible as-is.
  - README.md                                ✅ Compatible — README already
    describes the profile → discover → switch workflow; principles VI–VIII
    formalise existing intent rather than introducing new surface area.

Deferred TODOs:
  - The "outdated_patterns:" slot-YAML key in Principle VIII is not yet
    implemented in `bis/slots.py` or `bis/models.py`. This amendment
    establishes the contract; the schema migration is a separate feature.

History:
  1.0.0 — Initial ratification (2026-05-22). Five principles + Tech Stack
          Constraints + Skill / CLI Workflow + Governance.
  1.1.0 — Raise Python floor to ≥3.14 (2026-05-22).
  1.2.0 — Add product-purpose principles VI–VIII (2026-05-22).
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

### VI. Mine the User's History, Don't Ask for It
The first answer to "what should I use?" MUST come from the user's own GitHub
history, not from a generic recommendation. `bis profile` is the canonical
source for initial picks: slot defaults MUST be derived from frequency ×
recency of real usage across the user's repos (user + orgs, public + private).
A slot pick that is not traceable to a profile signal MUST be marked with a
`source:` field in the slot YAML (e.g. `source: profile`, `source: manual`,
`source: default`) and surfaced in `bis status`. Asking the user to declare
their stack from scratch — when a profile already exists — is a failure mode,
not a fallback.
**Rationale:** The product's whole edge over a static "awesome-X" list is that
it grounds every claim in the user's actual code. Letting that signal degrade
— even by silently accepting a pick the profile contradicts — destroys the
differentiator.

### VII. Surface New Winners, Not Just Catalogue Old Ones
`bis discover` MUST proactively flag the case where a candidate scores
meaningfully higher than the current pick on dimensions that overlap the
user's profile signal. When such a flag fires, the skill layer MUST emit a
short TL;DR update — current pick, candidate, the 2–3 signals that flipped,
and a suggested action — not a wall of analysis. The "meaningfully higher"
threshold MUST be a named constant in code (not a per-invocation argument),
versioned alongside the scoring weights. Stale-slot detection (configurable
threshold in `settings.yaml`) MUST run on every `bis status` invocation so a
stale winner cannot hide between explicit `bis discover` runs.
**Rationale:** A tool that requires the user to *ask* whether something has
changed is no better than a bookmark. The product is the proactive nudge —
delivered as a TL;DR, not a research paper.

### VIII. Flag Outdated In-Package Usage
Beyond cross-package swaps, BIS MUST detect outdated *intra*-package patterns
— legacy APIs, deprecated config keys, pre-major-version idioms — inside
packages the user still depends on (e.g. Pydantic v1 syntax in a Pydantic v2
install, `requests.Session` patterns in code that has already migrated to
`httpx`, Pandas `.append()` calls). Detected patterns MUST be recorded against
the relevant slot under an `outdated_patterns:` key, each entry citing the
modern equivalent and a stable reference (changelog, upgrade guide, or
release notes URL). The CLI MUST expose them via `bis status` and/or a
dedicated subcommand; the skill layer MUST translate them into actionable
diffs the user can apply, not just prose.
**Rationale:** "Right package, wrong decade" is the silent killer of
codebases. Swapping libraries is loud and shows up in dependency files;
staying on a library while its idioms move is invisible to every other tool —
exactly the gap BIS is positioned to close.

## Tech Stack Constraints

- **Language/Version:** Python ≥ 3.14. No Python 2, no untyped code paths in
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
  category, a scoring dimension, an outdated-pattern detector, or a
  profile-derivation signal MUST be checked against Principles I–VIII before
  merge. The Constitution Check gate in `plan-template.md` enforces this for
  spec-kit-driven features.
- Complexity must be justified. If a feature appears to require violating a
  principle, the PR MUST include a "Complexity Justification" section
  explaining why no compliant design exists. Reviewers SHOULD push back on
  unjustified violations.

**Version**: 1.2.0 | **Ratified**: 2026-05-22 | **Last Amended**: 2026-05-22
