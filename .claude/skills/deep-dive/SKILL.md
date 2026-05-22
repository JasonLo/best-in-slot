---
name: deep-dive
description: Produces an opinionated, evidence-backed deep-dive on one tool already slotted in `slots/`, combining (1) how Jason actually uses the tool across his GitHub repos (public, private, and orgs) with (2) what's new in the latest upstream version pulled from the live web. Appends a dated `## Deep dive` section to the slot's README; never rewrites the curated body above. Use when the user asks for a deep dive, deeper look, refresh, or "what's new" on a specific slotted tool — e.g. "deep dive on uv", "deeper look at fastmcp", "refresh the pydantic slot", "what's new in ty".
---

# deep-dive

A one-page, dated supplement to a slot's README — grounded in real code and current docs, not vibes.

## Inputs

- **One** tool name from the user (the thing being deep-dived). If they mention more than one, ask which.
- GitHub identity: `jasonlo`. Mining mode is auto-detected in step 2 — Mode A (full `gh`), Mode B (GitHub MCP), or Mode C (local repo only). Don't ask the user; probe.

## Steps

### 1. Resolve the slot

- Search the repo: `grep -nE "slots/[^)]*<tool>" README.md` and `ls -d slots/*/<tool>` from the repo root.
- If the slot doesn't exist, stop and tell the user — this skill is for refreshing existing slots, not adding new ones.
- If multiple candidates match (e.g. user said "mcp" and we have `fastmcp`), ask which before continuing.
- Read the slot's `README.md` and `CHEATSHEET.md` so the deep dive complements them instead of repeating them.

### 2. Mine Jason's GitHub usage

Do this BEFORE touching docs — the goal is to anchor recommendations in what he actually writes.

Pick the **first mode below that works in your environment** and prepend the matching caveat line to the "Your usage patterns" section. Don't silently fall through — name which mode you used.

#### Mode A — full GitHub mining (preferred, requires authenticated `gh`)

- Probe: `gh auth status`. If that errors or returns "not logged in", skip to Mode B.
- Discover scope: `gh api user/orgs --jq '.[].login'` for org list; treat `user:jasonlo` plus each org as the search universe.
- Find candidate repos: `gh repo list jasonlo --limit 200 --json name,description,pushedAt,language,visibility,primaryLanguage`. Repeat for each org. Sort by `pushedAt` descending.
- Search code, scoped per universe (run as many of these as match the tool's shape):
  - Python lib: `gh search code "from <module>" user:jasonlo` and `"import <module>"`; then once per org with `org:<name>`.
  - CLI tool: `gh search code "<binary>" --filename "*.yml" user:jasonlo` (CI), `--filename Justfile`, `--filename Makefile`.
  - Pyproject deps: `gh search code "\"<pkg>\"" --filename pyproject.toml user:jasonlo`.
  - Settings / config: `gh search code "[tool.<name>]" --filename pyproject.toml user:jasonlo`.
- For the top 5–10 hits, fetch the full file (`gh api /repos/<owner>/<repo>/contents/<path> --jq '.content' | base64 -d`) and read it. Don't summarise from search snippets — they lie.
- No caveat needed if this mode succeeded.

#### Mode B — GitHub MCP mining (when `gh` is missing but a `mcp__github__*` toolset is available)

- Use whatever `mcp__github__search_code` / `mcp__github__get_file_contents` your host exposes. Check the system prompt's "Repository Scope" — if the MCP is restricted to a single repo, you're effectively Mode C; don't pretend otherwise.
- Caveat to prepend: `_GitHub mining via MCP (scope: <list of reachable repos>). Wider jasonlo-history scan not available in this environment._`

#### Mode C — single-repo fallback (no `gh`, MCP scoped to one repo, or both)

This is the degraded path. Recommendations come almost entirely from docs; the "Your usage patterns" section is reduced to "what's already in this slot."

- Grep the local working tree only: `git grep -nE "<symbols-the-tool-exposes>" -- 'slots/'`, `find slots -name pyproject.toml -exec grep -l "<pkg>" {} +`, etc. Read the matches.
- Treat the slot's own `example/` as the canonical usage sample.
- Caveat to prepend: `_No external GitHub history available in this environment — patterns below are taken from this repo only (slot example + cross-references). Recommendations weight current upstream docs more heavily than usual._`

#### Always capture (any mode)

- **Version pin** in use (from `pyproject.toml`, `package.json`, lockfile, or CI matrix).
- **Which features** are actually touched (specific imports, decorators, CLI flags, config keys).
- **Co-occurring slots** — what other tools live next to it in the same project.
- **Anti-patterns** — anything being done that the current docs now discourage.

If a search in your active mode returns nothing, say so explicitly. Don't fabricate patterns.

### 3. Pull current upstream docs (web only)

Try doc sources **in this order**. Marketing docs sites (`*.gofastmcp.com`, `docs.astral.sh`, `docs.pydantic.dev`, etc.) frequently return 403 to `WebFetch` from non-browser user agents; assume that's the default failure mode, not an exception. The project's own GitHub repo always works.

1. **Registry first** (~always works, gives you the version + release date so you know what to look for):
   - `WebFetch https://pypi.org/project/<pkg>/` (or `npmjs.com/package/<pkg>`, `crates.io/crates/<pkg>`).
   - Note the version and release date. If it shipped after the user's pin, there's news to report.
2. **GitHub repo's `/docs/` tree** (markdown / mdx — always renders, no 403):
   - `WebFetch https://github.com/<owner>/<repo>/blob/main/README.md` for the top-level overview and feature list.
   - `WebFetch https://github.com/<owner>/<repo>/blob/main/docs/<area>.mdx` for deep pages. Common paths to try: `docs/getting-started/...`, `docs/deployment/...`, `docs/servers/...`, `docs/integrations/...`, `docs/patterns/...`. Don't guess all of them — `WebSearch "<tool> <feature> site:github.com"` first if the path isn't obvious.
   - If a path 404s, recover via `WebSearch "<tool> <feature>"` and follow the first GitHub-hosted hit.
3. **GitHub releases / CHANGELOG**:
   - `WebFetch https://github.com/<owner>/<repo>/releases` or `.../blob/main/CHANGELOG.md`.
   - This is how you learn which features arrived since the user's pinned version.
4. **Marketing docs site as fallback only** (`gofastmcp.com`, `docs.astral.sh`, `docs.pydantic.dev`, etc.):
   - Expect 403. Try once with `WebFetch`; if blocked, link to the page from the deep-dive section anyway (the user will read it in a browser) but don't claim to have read it.
5. **WebSearch** is the safety net when you don't know where a feature lives.

Capture URLs you actually fetched (so the section's docs links are verified-good) separately from URLs you couldn't reach but are pointing the user at — mark unverified ones in your internal notes, not in the final section.

Don't rely on training knowledge of the tool — assume it has moved since you last saw it.

### 4. Synthesise

Append exactly one section to `slots/<category>/<tool>/README.md` using this skeleton. Use today's date (ISO `YYYY-MM-DD`). Keep it under ~250 lines of markdown — this is a one-page refresh, not a manual.

```markdown
## Deep dive (YYYY-MM-DD)

_Generated by `.claude/skills/deep-dive` against <tool> v<X.Y.Z> (released <date>, latest as of <today>). Mining mode: <A | B | C>._

### Your usage patterns

<Mode A: omit caveat. Mode B/C: include the matching caveat line from step 2.>

- `<owner>/<repo>` `path/to/file.py:L<line>` — <one-line description of what he does>.
- … (5–10 bullets, every one citing a path)
- **Version pins seen**: `<repo-a>` pins `>=X`, `<repo-b>` pins `^Y`, …
- **Recurring combos**: shows up alongside <slot>, <slot>, <slot>.

### What's new since you last touched it

- **<feature>** (added in vX.Y) — <one-line description>. Docs: <link>.
- … (only items added since his current pin, OR features he isn't yet using)

### Recommendations

1. **<concrete action>** — why it's worth doing, and which of his repos/files it applies to. Reference the specific line if there's an obvious place to drop it in.
2. … (3–6 items, ranked by impact)

### Usage example

\`\`\`<lang>
<minimal runnable snippet showing the top recommendation, mirroring CHEATSHEET style>
\`\`\`

### Use cases

- Reach for this when …
- Don't reach for this when … (point at the alternative slot if there is one)

### Tradeoffs

- **<this tool's choice>** vs **<alternative>**: <when each wins>.
- … (2–4 bullets)
```

### 5. Apply and report

- Append the new section to the bottom of `slots/<category>/<tool>/README.md`. If a prior `## Deep dive (...)` section is already there, add the new one *after* it (chronological, newest last) — never delete prior dives.
- Show the resulting diff (`git diff -- slots/<category>/<tool>/README.md`).
- Do **not** commit. The user can decide if it's worth keeping.

## Guardrails

- **Cite everything in "Your usage patterns".** Every bullet has a `owner/repo path:line` citation. No citation → drop the bullet.
- **Quote private code sparingly.** ≤ 5 lines from any private repo, and prefer paraphrase. Public repos can be quoted freely.
- **One tool per invocation.** If the user asks for three, run three times.
- **Stay additive.** The curated README body above the deep-dive section is the contract for the slot. Don't touch it from this skill.
- **Be honest about gaps.** Empty GH search → say so. Couldn't reach docs → say so. Version pin missing in a repo → say "no pin found".
- **No marketing copy.** Match the project's voice: terse, opinionated, evidence-first.

## Don't

- Don't run on a tool that isn't already slotted. Tell the user to add the slot first.
- Don't fetch from blog posts, Medium, or LinkedIn — only official docs, the project's GitHub repo, and Jason's own code.
- Don't merge this into the CHEATSHEET. CHEATSHEET is curated and stable; the deep dive is a dated snapshot that can stale-out gracefully.
- Don't infer "best practices" from the docs alone — every recommendation has to point at something Jason can change in a specific file, or be marked as speculative.
