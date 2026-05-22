# Quickstart: Bootstrap Discovery Pipeline

**Audience**: A developer who has just cloned this repo and wants to go from zero slots to a confirmed, deep-dived slot set.

**Prerequisites**:
- `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- `gh` CLI installed and authenticated (`gh auth status` succeeds)
- Read access to the GitHub repos / orgs you want included (the bootstrap will skip what it cannot read and report what was skipped)

---

## First run (CLI — one-shot)

```bash
uv sync                            # install pinned deps
uv run bis init               # interactive walk-through (mine + walk in one shot)
```

What you'll see:

1. **Mining phase** — progress like `Scanning owner/repo (12/47)…`. First run takes a few minutes for ≤50 repos; subsequent runs within 24h hit the cache and finish in seconds (SC-009).
2. **Existing-state check** — if any `slots/*.yaml` files already exist, the CLI pauses and asks `merge / replace / skip`. Pick one explicitly.
3. **Walk-through** — proposals appear one slot at a time, in the order: languages → frameworks → tooling. Powered by `questionary` (arrow keys + Enter, sub-second per-slot latency — SC-011). Pick `change pick` to type any package name (observed or not — Q1 clarification).
4. **Per-slot deep-dive offer** — after each accept/change: `Run /deep-dive on this slot now? [y/n/a=all-later/x=skip-all]`. `/deep-dive` is invoked by the skill layer; in raw CLI mode this offer can be skipped with `--no-deep-dive-prompt`.
5. **Run summary** — counts of accepted/changed/skipped/deferred, plus any skipped sources (FR-008).

---

## First run (CLI — two-step mine + walk, US5)

For scripted/skill use, the two-step flow gives you a clean handoff point between the mining stage (where the LLM helps with category inference on unknowns) and the walk-through (where the LLM is out of the loop entirely):

```bash
uv run bis init mine --json   # mine + propose; persists slots/.bootstrap.yaml; emits proposals
uv run bis init walk          # fast local walk-through over the persisted proposals
```

Why split it? **Speed.** When `/bis-bootstrap` drove the per-slot loop conversationally, every accept/change/skip/defer cost one LLM turn (~5–15s × ~12 slots = 2–4 min of waiting). With `mine` + `walk`, the LLM is involved once (mining), then you drive the picks at native CLI speed. Target: ≤30s total LLM-active wall-clock per session (SC-012), and p95 < 200ms per-slot decision latency (SC-011).

`bis init walk` is idempotent and resumable — if you `Ctrl-C` mid-walk, `pending_proposals` is preserved in `slots/.bootstrap.yaml` and re-running `bis init walk` picks up where you left off (no re-mining).

---

## First run (Claude skill)

In Claude Code:

```
/bis-bootstrap
```

The skill uses the two-step `mine` + `walk` flow above. Total LLM turns per session: ≤3 (mine → handoff prompt → final summary + batched `/deep-dive` offer). The per-slot walk happens in your terminal — the skill steps out of the way during it.

---

## Aborting and resuming

Press Ctrl-C at any prompt. Already-confirmed slots are persisted; undecided slots become `deferred` in `slots/.bootstrap.yaml`. Structural edits (US4 — see below) are also persisted as `taxonomy_edits` and **replayed** against the freshly-mined proposal set on the next run.

Re-run `uv run bis init` later — deferred slots appear at the **top** of the walk-through (R-9 / R-11), in the order they were deferred. Once decided, they leave the deferred list.

---

## Reshaping the slot structure (US4)

Sometimes the proposed taxonomy itself is wrong — not the pick within a slot, but the slot's shape. Real example: the original heuristic table lumped `uv`, `ruff`, `ty`, `pytest`, `ipykernel` into one `python-tooling` slot where the winner was decided by frequency (commit `3bc2482`). Splitting into 5 sub-slots — one per role — is a one-conversation operation:

### Pre-walk taxonomy review

```bash
uv run bis init taxonomy-review --json
```

Returns the full proposal list with `members` (proposed_pick + alternatives) and `suggest_split_into` per proposal. The skill renders this as a `[looks good / reshape]` prompt.

### Five structural actions

Each runs through `bis init confirm` with a structure-aware action:

```bash
# Split one slot into N sub-slots — system suggests a partition, OR pass --into
uv run bis init confirm --category python-tooling --action split --json
uv run bis init confirm --category my-mixed --action split --into a,b,c --json

# Merge one slot into another (must share category_type — see FR-019)
uv run bis init confirm --category type-checker --action merge --with linter-formatter --json

# Rename a slot label without changing membership
uv run bis init confirm --category databases --action rename --to-name datastore --json

# Drop a slot from the proposal set entirely (distinct from skip)
uv run bis init confirm --category python-terminal --action drop --json

# Add a slot the bootstrap didn't propose
uv run bis init confirm --category infra --action add --pick terraform --new-type tooling --json
```

Each successful structure action is recorded in `slots/.bootstrap.yaml`'s `taxonomy_edits` array (append-only). On the next bootstrap run, those edits are **replayed** against the freshly-mined proposal set — you don't have to redo the reshape after a fresh pull or 24h cache expiry.

### Restructure without re-mining

If you want to revisit only the taxonomy (no fresh mining), use the dedicated subcommand:

```bash
uv run bis init restructure --json
```

This re-emits the taxonomy review against the cached proposal set. Errors with `no_prior_proposal` if you've never run a bootstrap on this directory.

### Error envelopes specific to US4

| Code | Meaning | Fix |
| --- | --- | --- |
| `unknown_category` | Merge / rename / drop target doesn't exist in the current proposal set | Run `bis init --json --batch` to see available categories. |
| `split_not_supported` | The heuristic table can't partition this slot's members, and no `--into` was given | Pass `--into name1,name2,...` to supply your own partition. |
| `merge_incompatible_types` | The two slots have different `category_type` (e.g., framework vs tooling) — merge would conflate roles | Rename one first, or pick a target with the same type. |
| `no_prior_proposal` | `bis init restructure` invoked but no `slots/.bootstrap.yaml` exists | Run `bis init` first to mine a proposal set. |

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

- **"I want to revisit my deferred slots"** → just run `uv run bis init`; deferred slots are at the top.
- **"I want a fresh look at everything"** → `uv run bis init --on-existing=replace` (interactive) or pass `--on-existing` in batch mode. Old slot YAMLs are replaced; their history is preserved within the new file via a `bootstrap-replace` history entry.
- **"My package registry choices changed; I want to merge"** → `uv run bis init --on-existing=merge` keeps existing picks where the bootstrap proposes the same value and prompts for the rest.

---

## Verifying the privacy invariant (FR-013 / SC-008)

```bash
uv run pytest tests/unit/test_privacy_scrubber.py -v
```

This test asserts that the JSON serialisation of any `SafePayload` contains no manifest-body, no README content, and no repo path beyond the package layer — exactly the data flow guarantee from Q2.

If you want to hand-verify a single run:

```bash
uv run bis init --dry-run --print-llm-payloads | jq .
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
