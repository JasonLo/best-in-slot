# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync                                              # Install dependencies
uv run bis --help                                    # CLI help
uv run bis profile                                   # Build tech profile from GitHub repos
uv run bis init                                      # Bootstrap slots from profile
uv run bis status                                    # Show all current picks (table)
uv run bis show <category>                           # Show one slot in detail (YAML)
uv run bis evaluate <category> <package>             # Score package vs current pick (JSON)
uv run bis discover                                  # Find candidates for stale slots (JSON)
uv run bis switch <category> <package> -r "reason"   # Change current pick, records history
```

## Architecture

**Python + YAML + Skills hybrid** — "Python does data, Claude does judgment."

- `bis/` — Python package that fetches data, parses dependencies, scores packages, and manages YAML state. All CLI commands live here via Typer.
- `slots/*.yaml` — One file per tech category (e.g., `python-web-framework.yaml`). Stores current pick, alternatives with scores/pros/cons, and switch history.
- `skills/` — Claude Code SKILL.md files (symlinked from `.claude/skills`). Each skill invokes `uv run bis <command>`, then adds qualitative reasoning — researching docs, comparing APIs, writing recommendations.
- `profile.yaml` — Generated tech fingerprint. Built by scanning all GitHub repos (user + orgs) and parsing dependency files across languages.
- `settings.yaml` — Config: GitHub username/orgs, category list, staleness threshold.

### Data flow

`bis profile` scans GitHub repos → parses dependency files (pyproject.toml, package.json, go.mod, etc.) → aggregates into `profile.yaml` with frequency × recency ranking → `bis init` maps top packages to categories → creates `slots/*.yaml` → `bis evaluate`/`discover` score alternatives using profile data + registry metadata (PyPI/npm).

### Scoring dimensions (weighted)

Personal usage (0.3) · Community adoption (0.25) · Maintenance health (0.2) · Ecosystem fit (0.15) · Migration cost (0.1 — placeholder for Claude judgment).

## Key conventions

- **Typer** for CLI (not Click)
- **Pydantic v2** for all data models (`bis/models.py`)
- **httpx** for HTTP requests to registries
- **YAML** for all persistent data — no database
- **`gh api` subprocess** for GitHub API — avoids token management, relies on `gh auth`
- Dependency parsers in `bis/scanner.py` return `str → list[str]` of normalized package names
- `bis/slots.py` handles all YAML CRUD; slot files named `{category}.yaml`

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
