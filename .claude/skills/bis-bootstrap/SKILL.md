---
name: bis-bootstrap
description: Bootstrap a best-in-slot tech inventory from the user's last 3 years of GitHub activity (public + private + org repos). Mines repo manifests, proposes a slot structure grouped languages → frameworks → tooling, offers a pre-walk taxonomy review (split / merge / rename / drop / add) and a per-slot prompt (accept / change / skip / defer + structural actions), persists `slots/{category}.yaml` state, and offers `/deep-dive` per confirmed slot. Use when the user says "bootstrap my slots", "set up best-in-slot", "mine my repos", "reshape my slots", "bootstrap discovery", or invokes `/bis-bootstrap`.
---

# bis-bootstrap

Conversational driver over the `bis bootstrap` CLI. The CLI does the data work
(scan repos, parse manifests, propose categories, write YAML); this skill does
the judgment work (frame the proposal, ask the user, chain into `/deep-dive`).
Per project constitution: data in Python, judgment in skills, no duplication.

## When to use

User invokes `/bis-bootstrap` or says any of: "bootstrap my slots", "set up
best-in-slot", "mine my repos", "discover my tools", "bootstrap discovery".

If `slots/*.yaml` files already exist and the user just wants to revisit a
deferred slot or update one, this is still the right entry point — the
existing-state check below handles that path.

## Prerequisites — check first

Run these in parallel. If any fails, surface the gap and stop:

1. `gh auth status` — must exit 0. If not, instruct: `gh auth login`.
2. `which uv` — must exist. If not, instruct: install uv from
   https://astral.sh/uv.
3. `ls -d bis 2>/dev/null` — must exist. If the bis package isn't here, you're
   probably in the wrong directory.

## Flow

### Step 1 — Detect existing state

```bash
uv run bis bootstrap --json --batch
```

Possible outcomes:

- **Exit 0, `{"mode":"batch", "proposals":[...]}`** — fresh run, proceed to
  step 2 with the proposal list.
- **Exit 2, `{"mode":"error","error":{"code":"existing_state_unresolved"}}`** —
  slots already exist. Ask the user: `merge / replace / skip`. Then re-run with
  `--on-existing=<choice>`.
- **Exit 2, `{"mode":"error","error":{"code":"gh_auth_missing"}}`** — auth gap.
  Tell the user to `gh auth login` and stop.
- **Exit 2, `{"mode":"error","error":{"code":"no_repos_in_window"}}`** — no
  recent activity. Suggest widening the window in `settings.yaml` or seeding
  slots manually; stop.

### Step 2a — Pre-walk taxonomy review (FR-017, US4)

Before walking through picks, give the user a chance to reshape the taxonomy
itself. The proposed slots may be wrong at the structure level — a category
might lump multiple roles (the `python-tooling` → 5 sub-slots scenario from
commit `3bc2482`), two categories might be redundant, a label might be off,
or the user might want a slot the bootstrap didn't propose.

```bash
uv run bis bootstrap taxonomy-review --json
```

Render the result as a compact overview:

```
Proposed slot structure (N slots):
  • <category> (<category_type>) — <proposed_pick> [+N alternatives]
    suggested split: <suggest_split_into joined>     # only if present
  ...

Does this taxonomy look right? [looks good / let's reshape]
```

If the user picks **looks good**, skip to Step 2b.

If the user picks **let's reshape**, enter a sub-loop offering five
structural actions. Each one maps to a `bis bootstrap confirm` call:

| Action  | What it does                                          | CLI call                                                                              |
| ------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------- |
| split   | Break one slot into N sub-slots                       | `confirm --category X --action split [--into name1,name2,...]`                        |
| merge   | Fold one slot into another (must share category_type) | `confirm --category X --action merge --with Y`                                        |
| rename  | Change a slot's label without changing membership     | `confirm --category X --action rename --to-name Z`                                    |
| drop    | Remove a slot from the proposal set entirely          | `confirm --category X --action drop`                                                  |
| add     | Insert a custom slot the bootstrap didn't propose     | `confirm --category X --action add --pick PKG --new-type {language\|framework\|tooling}` |

Each successful structural change is recorded in
`slots/.bootstrap.yaml:taxonomy_edits` (append-only). On the next bootstrap
run, the edits are replayed against the freshly-mined proposal set so the
user doesn't have to redo them.

If the CLI returns one of the US4 error envelopes — `unknown_category`,
`split_not_supported`, `merge_incompatible_types`, `no_prior_proposal` —
surface the `message` + `hint` verbatim and let the user retry.

Stay in the reshape sub-loop until the user is satisfied, then proceed to
Step 2b with the rebuilt taxonomy.

### Step 2b — Walk through proposals

The batch payload contains `proposals: [CategoryProposal]` already ordered
languages → frameworks → tooling, with deferred slots at the top.

For each proposal, present this to the user (one slot at a time):

```
[idx/total] <category> — proposed pick: <proposed_pick>
            evidence: <repo_count> repos, most recent <evidence_most_recent>
            alternatives: <alternatives joined>
            <confidence_qualifier line if not None>

   Action? [a]ccept / [c]hange / [s]kip / [d]efer
   structural: split / merge / rename / drop      (optional, US4)
```

If the user picks **change**, present the observed alternatives as a numbered
list AND accept a free-form package name. The clarification (Q1 in spec) says
free-form input is allowed even for packages the user has never used.

If the user picks a **structural** action mid-walk-through, route it through
the Step 2a `confirm --action` table — the walk-through resumes against the
rebuilt taxonomy, re-ordered per FR-014. The user can also at any pause type
"add a custom slot" to insert one without splitting/merging an existing one.

When the user picks a pick action, apply it:

```bash
uv run bis bootstrap confirm --category <cat> --action <accept|change|skip|defer> [--pick <name>] --json --on-existing <choice>
```

### Step 3 — Offer /deep-dive per confirmed slot

After each `accept` or `change`, ask:

```
   Run /deep-dive on <category> → <pick> now? [y/n/all-later/skip-all]
```

- **y** — invoke `/deep-dive` with `<pick>` as the tool name.
- **n** — continue.
- **all-later** — collect the slot into a queue; at end of walk-through, ask
  whether to batch-dive the queue.
- **skip-all** — don't ask again for the rest of this run.

If a `/deep-dive` invocation fails for one slot, record `{category, error}` in
a local list and keep going — never abort the walk-through (FR-011).

### Step 4 — Final summary

When the walk-through ends, summarise:

- Pick counts: accepted, changed, skipped, deferred
- Structural changes (US4): one count each for split / merge / rename / drop / add
  applied during the run — read from the `taxonomy_edits` array in
  `slots/.bootstrap.yaml`
- Deep-dive failures (if any)
- Skipped sources (from the batch payload's `skipped_sources`)
- Pointer: `uv run bis bootstrap pending-dives --json` lists slots that still
  need a `/deep-dive` later

Example summary:

```
Walk-through complete.
  Picks: 8 accepted, 3 changed, 1 skipped, 0 deferred
  Structure: 1 split, 0 merge, 1 rename, 1 drop, 1 add (terraform → infra)
  Skipped sources: 1 (org:secret-corp — access denied)
  /deep-dive: 0 failures, 4 slots still pending (run `bis bootstrap pending-dives --json` to see them)
```

## Privacy posture

The user's clarification (Q2 in spec, FR-013, SC-008): only package names,
frequencies, and recency timestamps may cross the trust boundary. The CLI
enforces this via `bis/privacy.py:to_safe_payload`. The skill MUST NOT include
raw manifest content, README bodies, or repo identities beyond the package
layer in any LLM-bound message.

If the user asks "what would the LLM see?", point them at
`uv run bis bootstrap --dry-run --print-llm-payloads`.

## What this skill MUST NOT do

- Don't re-parse manifests in skill-land (the CLI's `bis/scanner.py` is
  authoritative — constitution Principle III).
- Don't hit the GitHub API directly (the CLI's `bis/github.py` is
  authoritative).
- Don't write `slots/*.yaml` directly (the CLI's `bis/slots.py` is
  authoritative).
- Don't invent `confidence_qualifier` values; pass through whatever the CLI
  returns.
- Don't bypass the per-slot user prompt and bulk-accept. Every confirmed slot
  must cross the user's eyes (spec Assumptions: "interactive by design").

## Trigger phrases (for natural-language invocation)

bootstrap my slots · set up best-in-slot · mine my repos · discover my tools ·
bootstrap discovery · slot setup · audit my stack from scratch · reshape my
slots · restructure my taxonomy · split this slot · merge these slots · add a
custom slot
