---
name: bis-bootstrap
description: Bootstrap a best-in-slot tech inventory from the user's last 3 years of GitHub activity (public + private + org repos). Mines repo manifests, proposes a slot structure grouped languages → frameworks → tooling, offers a pre-walk taxonomy review (split / merge / rename / drop / add), and then HANDS OFF to a fast local walk-through (`bis init walk`, powered by questionary — arrow keys + Enter, no LLM in the loop) so per-slot picks happen at native terminal speed. Re-engages once at the end to offer batched `/deep-dive` over the confirmed slots. Use when the user says "bootstrap my slots", "set up best-in-slot", "mine my repos", "reshape my slots", "bootstrap discovery", or invokes `/bis-bootstrap`.
---

# bis-bootstrap

Two-phase wrapper over the `bis init` CLI:

1. **LLM phase (≤2 turns)** — drive `bis init mine` (with optional pre-walk `taxonomy-review` reshape) so the proposal set lands on disk in `slots/.bootstrap.yaml`.
2. **Hand-off → local CLI** — the user runs `bis init walk` in their terminal; `questionary` drives the per-slot picks with sub-second response. The LLM is OUT of the loop here. This is the key UX win: per-slot decisions happen at native CLI speed instead of one-LLM-turn-per-slot.
3. **LLM phase (1 turn)** — once the walk completes, offer batched `/deep-dive` over the confirmed slots in one prompt.

Total LLM turns per session: ≤3 (vs the prior loop's one-per-slot). Per project constitution: data in Python, judgment in skills, no duplication. Trust boundary FR-013 unchanged — only `SafePayload` payloads cross.

## When to use

User invokes `/bis-bootstrap` or says any of: "bootstrap my slots", "set up best-in-slot", "mine my repos", "discover my tools", "bootstrap discovery".

If `slots/*.yaml` files already exist and the user wants to revisit a deferred slot or update one, this is still the right entry point — the existing-state check below handles that path.

## Prerequisites — check first

Run these in parallel. If any fails, surface the gap and stop:

1. `gh auth status` — must exit 0. If not, instruct: `gh auth login`.
2. `which uv` — must exist. If not, instruct: install uv from https://astral.sh/uv.
3. `ls -d bis 2>/dev/null` — must exist. If the bis package isn't here, you're probably in the wrong directory.

## Flow

### Step 1 — Mine proposals (1 LLM turn)

```bash
uv run bis init mine --json
```

Possible outcomes:

- **Exit 0, `{"mode":"mine", "proposals":[...], "pending_proposals_count": N, ...}`** — proposals persisted to `slots/.bootstrap.yaml`; proceed to Step 2.
- **Exit 2, `{"mode":"error","error":{"code":"existing_state_unresolved"}}`** — slots exist. Ask the user: `merge / replace / skip`. Re-run with `--on-existing=<choice>`.
- **Exit 2, `gh_auth_missing`** — tell the user to `gh auth login` and stop.
- **Exit 2, `no_repos_in_window`** — suggest widening the window in `settings.yaml`; stop.

### Step 2 — Optional pre-walk taxonomy reshape (FR-017, US4)

Only enter this branch if the proposal list looks structurally wrong (a slot lumps multiple roles, two slots are redundant, etc.). Most users skip it.

```bash
uv run bis init taxonomy-review --json
```

Render a compact overview and ask `[looks good / let's reshape]`. If the user picks **reshape**, apply structural actions via `bis init confirm`:

| Action  | What it does                                          | CLI call                                                                              |
| ------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------- |
| split   | Break one slot into N sub-slots                       | `confirm --category X --action split [--into name1,name2,...]`                        |
| merge   | Fold one slot into another (must share category_type) | `confirm --category X --action merge --with Y`                                        |
| rename  | Change a slot's label without changing membership     | `confirm --category X --action rename --to-name Z`                                    |
| drop    | Remove a slot from the proposal set entirely          | `confirm --category X --action drop`                                                  |
| add     | Insert a custom slot the bootstrap didn't propose     | `confirm --category X --action add --pick PKG --new-type {language\|framework\|tooling}` |

Each structural change is recorded in `slots/.bootstrap.yaml:taxonomy_edits` (append-only) and replayed on the next bootstrap.

When the user is done reshaping, re-run `bis init mine` so the taxonomy edits replay onto a fresh proposal set, then continue to Step 3.

### Step 3 — Hand off to the local walk-through

This is the speed win. Surface a single prompt to the user (do NOT iterate proposals here):

```
Mined N proposals. The next step is a local walk-through powered by `questionary`
(arrow keys + Enter, sub-second per slot — no LLM in the loop).

Run this command in your terminal:

    uv run bis init walk

When you've finished, come back here and tell me you're done so I can offer
/deep-dive over the confirmed slots.
```

Then wait. **DO NOT iterate proposals conversationally**. The walk lives entirely in the user's terminal — the skill's job here is to step out of the way.

If the user `Ctrl-C`s mid-walk, `bis init walk` emits `walk_aborted` and preserves `pending_proposals` so they can resume by re-running the same command. No re-mining required.

### Step 4 — Offer batched /deep-dive (1 LLM turn)

After the user reports the walk is complete, read the confirmed slots:

```bash
uv run bis init pending-dives --json
```

Surface the list once with a single prompt:

```
Walk complete. Confirmed slots awaiting /deep-dive:
  - python-web → fastapi
  - python-lint → ruff
  - python-pkg → uv
  ...

Run /deep-dive on:
  [a] all of them
  [n] none — I'll do it later
  [s] select a subset
```

On **all**, invoke `/deep-dive` once per slot (the deep-dive itself is per-slot, but the *prompt* to the user is one turn). On **none**, summarise and end. On **select**, ask the user which subset.

Failures in any single `/deep-dive` invocation are collected and reported in the final summary (FR-011).

### Step 5 — Final summary

Render once:

```
Bootstrap complete.
  Picks: A accepted, C changed, S skipped, D deferred  (from `bis init walk` output)
  Skipped sources: ...                                 (from `bis init mine` output)
  /deep-dive: F failures, P slots still pending
```

## Privacy posture

FR-013 / SC-008 unchanged. Only package names, frequencies, and recency timestamps may cross the trust boundary, enforced by `bis/privacy.py:to_safe_payload`. The hand-off does NOT introduce any new LLM-bound payload — the walk-through is entirely local. The skill MUST NOT include raw manifest content, README bodies, or repo identities beyond the package layer in any LLM-bound message.

If the user asks "what would the LLM see?", point them at the `SafePayload` items in the `bis init mine` JSON output.

## What this skill MUST NOT do

- **Don't iterate proposals conversationally.** The per-slot loop is the local CLI's job (`bis init walk`). The skill's job is to mine, hand off, and re-engage at the end. ≤3 LLM turns per session.
- **Don't call `bis init confirm` per slot during the walk.** That path is for one-off scripted decisions (e.g., during a `restructure` flow), not for driving the main walk-through.
- Don't re-parse manifests in skill-land (constitution Principle III).
- Don't hit the GitHub API directly (`bis/github.py` is authoritative).
- Don't write `slots/*.yaml` directly (`bis/slots.py` is authoritative).
- Don't invent `confidence_qualifier` values; pass through whatever the CLI returns.

## Trigger phrases (for natural-language invocation)

bootstrap my slots · set up best-in-slot · mine my repos · discover my tools · bootstrap discovery · slot setup · audit my stack from scratch · reshape my slots · restructure my taxonomy · split this slot · merge these slots · add a custom slot
