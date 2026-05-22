# Quickstart: Bootstrap Discovery Pipeline

**Audience**: A developer who has just cloned this repo and wants to go from zero slots to a confirmed, deep-dived slot set.

**Prerequisites**:
- `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- `gh` CLI installed and authenticated (`gh auth status` succeeds)
- Read access to the GitHub repos / orgs you want included (the bootstrap will skip what it cannot read and report what was skipped)

---

## First run (CLI)

```bash
uv sync                            # install pinned deps
uv run bis bootstrap               # interactive walk-through
```

What you'll see:

1. **Mining phase** — progress like `Scanning owner/repo (12/47)…`. First run takes a few minutes for ≤50 repos; subsequent runs within 24h hit the cache and finish in seconds (SC-009).
2. **Existing-state check** — if any `slots/*.yaml` files already exist, the CLI pauses and asks `merge / replace / skip`. Pick one explicitly.
3. **Walk-through** — proposals appear one slot at a time, in the order: languages → frameworks → tooling. For each:
   ```
   [3/12] python-web — proposed pick: fastapi
          evidence: 8 repos, most recent 2026-04-12
          alternatives observed: django, litestar
   
          action? [a]ccept / [c]hange / [s]kip / [d]efer >
   ```
   Pick `c` to type any package name (observed or not — Q1 clarification).
4. **Per-slot deep-dive offer** — after each accept/change: `Run /deep-dive on this slot now? [y/n/a=all-later/x=skip-all]`. `/deep-dive` is invoked by the skill layer; in raw CLI mode this offer can be skipped with `--no-deep-dive-prompt`.
5. **Run summary** — counts of accepted/changed/skipped/deferred, plus any skipped sources (FR-008).

---

## First run (Claude skill)

In Claude Code:

```
/bis-bootstrap
```

Same flow, but the walk-through happens in conversation. The skill calls `bis bootstrap --json --batch` once to get the proposals, then walks you through them. Deep-dive prompts use the existing `/deep-dive` skill seamlessly.

---

## Aborting and resuming

Press Ctrl-C at any prompt. Already-confirmed slots are persisted; undecided slots become `deferred` in `slots/.bootstrap.yaml`.

Re-run `uv run bis bootstrap` later — deferred slots appear at the **top** of the walk-through (R-9 / R-11), in the order they were deferred. Once decided, they leave the deferred list.

---

## Inspecting state

```bash
ls slots/*.yaml                              # confirmed slot state (one file per category)
cat slots/.bootstrap.yaml                    # last run's deferred slots + skipped sources
ls .bis/cache/repos/                         # per-repo mining cache (gitignored)
uv run bis status                            # tabular view of all picks (added by this feature)
```

---

## Re-running the bootstrap

Run again any time. The cache means it's cheap. Common scenarios:

- **"I want to revisit my deferred slots"** → just run `uv run bis bootstrap`; deferred slots are at the top.
- **"I want a fresh look at everything"** → `uv run bis bootstrap --on-existing=replace` (interactive) or pass `--on-existing` in batch mode. Old slot YAMLs are replaced; their history is preserved within the new file via a `bootstrap-replace` history entry.
- **"My package registry choices changed; I want to merge"** → `uv run bis bootstrap --on-existing=merge` keeps existing picks where the bootstrap proposes the same value and prompts for the rest.

---

## Verifying the privacy invariant (FR-013 / SC-008)

```bash
uv run pytest tests/unit/test_privacy_scrubber.py -v
```

This test asserts that the JSON serialisation of any `SafePayload` contains no manifest-body, no README content, and no repo path beyond the package layer — exactly the data flow guarantee from Q2.

If you want to hand-verify a single run:

```bash
uv run bis bootstrap --dry-run --print-llm-payloads | jq .
```

`--dry-run` does mining + proposal but writes nothing; `--print-llm-payloads` dumps every `SafePayload` that *would* have been sent to the LLM during this run.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `error: gh_auth_missing` | `gh` not authenticated | `gh auth login` |
| `error: no_repos_in_window` | No activity in trailing 3 years | Use a fresh GH account? Wait. Seed `slots/*.yaml` manually. |
| `error: existing_state_unresolved` (batch mode) | Slots already exist, no `--on-existing` given | Add `--on-existing={merge,replace,skip}` |
| Mining feels slow on a re-run | Cache TTL expired (>24h) | Expected. Run is cold; SC-009 only promises cheap restarts *within* 24h. |
| One org's repos didn't appear in the proposal | Token scope missing for that org | `gh auth refresh -s read:org`; that org will appear in `skipped_sources` until then. |
