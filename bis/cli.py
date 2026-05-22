"""Typer CLI entry point for `bis`.

The CLI stays thin: argument parsing, JSON envelope construction, and prompt
loops. Orchestration logic lives in `bis.bootstrap`.

Output contract (machine-readable modes) is validated against
`specs/001-bootstrap-discovery/contracts/bootstrap.schema.json`.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from typing import Annotated, Literal, NoReturn, cast

import typer

from bis.bootstrap import (
    apply_decision,
    clear_deferral,
    detect_existing_state,
    end_run_state,
    mine_profile,
    proposals_for_walkthrough,
    record_deferral,
    record_structure_change,
    start_run_state,
)
from bis.categories import suggest_split
from bis.config import load_settings
from bis.models import (
    CategoryProposal,
    CategoryType,
    CliError,
    DecisionAction,
    ErrorCode,
    EvidenceBlock,
    HistoryEntry,
    ProfileSnapshot,
    SlotDecision,
    SlotState,
    StructureChange,
    StructureKind,
)
from bis.slots import read_bootstrap_run_state, write_slot_state

app = typer.Typer(
    name="bis",
    help="best-in-slot: personal tech-stack inventory and bootstrap pipeline.",
    no_args_is_help=True,
    add_completion=False,
)

bootstrap_app = typer.Typer(
    name="bootstrap",
    help="Bootstrap a slot structure from your GitHub repo history.",
    no_args_is_help=False,
)
app.add_typer(bootstrap_app)


# --------------------------------------------------------------------------- helpers


def _emit_json(payload: dict, *, exit_code: int = 0) -> NoReturn:
    sys.stdout.write(json.dumps(payload, default=_json_default) + "\n")
    sys.stdout.flush()
    raise typer.Exit(code=exit_code)


def _emit_error(code: ErrorCode, message: str, hint: str | None = None) -> NoReturn:
    err = CliError(code=code, message=message, hint=hint)
    _emit_json({"mode": "error", "error": err.model_dump(exclude_none=True)}, exit_code=2)


def _json_default(obj):  # noqa: ANN001
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _proposal_to_dict(p: CategoryProposal) -> dict:
    return p.model_dump(mode="json", exclude_none=True)


# --------------------------------------------------------------------------- bootstrap (interactive default)


@bootstrap_app.callback(invoke_without_command=True)
def bootstrap_root(
    ctx: typer.Context,
    json_mode: Annotated[
        bool, typer.Option("--json", help="Emit JSON-only output (machine-readable).")
    ] = False,
    batch: Annotated[
        bool, typer.Option("--batch", help="Non-interactive: emit the full proposal set and exit.")
    ] = False,
    on_existing: Annotated[
        str | None,
        typer.Option(
            "--on-existing",
            help="What to do when slots already exist: merge / replace / skip. Required in batch mode if slots exist.",
        ),
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Mine + propose but do not persist anything.")
    ] = False,
) -> None:
    """Run the bootstrap pipeline (interactive walk-through by default)."""

    if ctx.invoked_subcommand is not None:
        return

    settings = load_settings()
    existing = detect_existing_state()
    if existing and on_existing is None:
        if batch:
            _emit_error(
                "existing_state_unresolved",
                f"slots already exist for: {', '.join(existing)}",
                hint="re-run with --on-existing={merge,replace,skip}",
            )
        on_existing = typer.prompt(
            f"Slots already exist for {', '.join(existing)}. merge / replace / skip?",
            default="merge",
        )
    if on_existing not in (None, "merge", "replace", "skip"):
        _emit_error("existing_state_unresolved", f"invalid --on-existing={on_existing!r}")

    if on_existing == "skip" and existing:
        if json_mode:
            _emit_json(
                {
                    "mode": "batch",
                    "run_id": "",
                    "started_at": datetime.now(UTC),
                    "proposals": [],
                    "skipped_sources": [],
                    "on_existing_choice": "skip",
                }
            )
        typer.echo("Bootstrap skipped (existing slots preserved).")
        raise typer.Exit(0)

    # The validity guard above narrows on_existing to the Literal union, but
    # typer infers `str | None` from the option type, so cast for ty.
    run = start_run_state(
        on_existing_choice=cast("Literal['merge', 'replace', 'skip'] | None", on_existing)
    )

    try:
        profile = mine_profile(settings)
    except Exception as exc:  # noqa: BLE001 — surface as scanner_failed
        _emit_error("scanner_failed", str(exc))

    # Auth-missing surfaces via a synthetic SkippedSource with source_id="auth"
    auth_skip = next((s for s in profile.skipped_sources if s.source_id == "auth"), None)
    if auth_skip:
        _emit_error("gh_auth_missing", auth_skip.reason, hint="run `gh auth login`")

    if not profile.repos:
        _emit_error(
            "no_repos_in_window",
            "no repository activity found in the mining window",
            hint="broaden the window in settings.yaml or seed slots manually",
        )

    proposals = proposals_for_walkthrough(profile, deferred=run.deferred_categories)

    if json_mode and batch:
        end_run_state(run, profile.skipped_sources)
        _emit_json(
            {
                "mode": "batch",
                "run_id": run.run_id,
                "started_at": run.started_at,
                "proposals": [_proposal_to_dict(p) for p in proposals],
                "skipped_sources": [s.model_dump() for s in profile.skipped_sources],
                "on_existing_choice": on_existing,
                "deferred_categories_resurfaced": list(run.deferred_categories),
            }
        )

    # Interactive walk-through.
    _interactive_walkthrough(
        proposals, profile, run, on_existing=on_existing or "merge", dry_run=dry_run
    )
    end_run_state(run, profile.skipped_sources)


def _interactive_walkthrough(
    proposals: list[CategoryProposal],
    profile: ProfileSnapshot,
    run,
    *,
    on_existing: str,
    dry_run: bool,
) -> None:
    if not proposals:
        typer.echo("No proposals to walk through.")
        return

    typer.echo(f"Walk-through: {len(proposals)} slot(s) to review.")
    for idx, p in enumerate(proposals, 1):
        typer.echo("")
        typer.echo(f"[{idx}/{len(proposals)}] {p.category} — proposed pick: {p.proposed_pick}")
        typer.echo(
            f"        evidence: {p.evidence_repo_count} repos, most recent {p.evidence_most_recent.date()}"
            + (f" ({p.confidence_qualifier})" if p.confidence_qualifier else "")
        )
        if p.alternatives:
            typer.echo(f"        alternatives: {', '.join(p.alternatives)}")
        action = (
            typer.prompt("        action? [a]ccept / [c]hange / [s]kip / [d]efer", default="a")
            .strip()
            .lower()
        )
        if action.startswith("d"):
            run = record_deferral(run, p.category)
            continue
        if action.startswith("s"):
            clear_deferral(run, p.category)
            continue
        chosen = p.proposed_pick
        if action.startswith("c"):
            chosen = (
                typer.prompt("        new pick (type any package name)").strip() or p.proposed_pick
            )
        decision = SlotDecision(
            category=p.category,
            action="accept" if action.startswith("a") else "change",
            chosen_pick=chosen,
            was_proposal_unchanged=(chosen == p.proposed_pick),
        )
        if not dry_run:
            apply_decision(decision, p, on_existing=on_existing)
        clear_deferral(run, p.category)


# --------------------------------------------------------------------------- confirm subcommand


@bootstrap_app.command("pending-dives")
def bootstrap_pending_dives(
    json_mode: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = True,
) -> None:
    """List confirmed slots that have not yet received a /deep-dive enrichment.

    A slot is considered "dived" if `slots/{category}/{pick}/README.md` exists
    AND contains a `## Deep dive` heading (the marker the existing /deep-dive
    skill appends).
    """

    from bis.slots import list_existing_slot_categories, read_slot_state, slots_root

    pending: list[dict] = []
    for category in list_existing_slot_categories():
        state = read_slot_state(category)
        if state is None:
            continue
        readme = slots_root() / category / state.pick / "README.md"
        if not readme.exists() or "## Deep dive" not in readme.read_text():
            pending.append({"category": category, "pick": state.pick, "readme": str(readme)})

    if json_mode:
        _emit_json({"mode": "pending-dives", "pending": pending})
    for entry in pending:
        typer.echo(f"{entry['category']} → {entry['pick']} (no deep-dive yet)")


_VALID_ACTIONS = {"accept", "change", "skip", "defer", "split", "merge", "rename", "drop", "add"}
_PICK_ACTIONS = {"accept", "change", "skip", "defer"}
_STRUCTURE_ACTIONS = {"split", "merge", "rename", "drop", "add"}


@bootstrap_app.command("confirm")
def bootstrap_confirm(
    category: Annotated[str, typer.Option("--category", help="Slot category.")],
    action: Annotated[
        str,
        typer.Option(
            "--action",
            help="accept | change | skip | defer | split | merge | rename | drop | add.",
        ),
    ],
    pick: Annotated[
        str | None,
        typer.Option("--pick", help="The chosen package name (required for accept/change/add)."),
    ] = None,
    json_mode: Annotated[bool, typer.Option("--json", help="Emit JSON-only output.")] = True,
    on_existing: Annotated[str, typer.Option("--on-existing", help="merge | replace.")] = "merge",
    into: Annotated[
        str | None,
        typer.Option(
            "--into",
            help="Split: comma-separated sub-category names. Omit to use suggest_split.",
        ),
    ] = None,
    merge_with: Annotated[
        str | None,
        typer.Option("--with", help="Merge target — the category absorbing this one."),
    ] = None,
    to_name: Annotated[
        str | None,
        typer.Option("--to-name", help="Rename: the new category label."),
    ] = None,
    new_type: Annotated[
        str | None,
        typer.Option(
            "--new-type",
            help="Add: category_type for the new slot (language | framework | tooling).",
        ),
    ] = None,
) -> None:
    """Apply a single user decision (used by the bootstrap skill / scripts).

    Supports both pick-level actions (accept/change/skip/defer) and US4
    structural actions (split/merge/rename/drop/add).
    """

    if action not in _VALID_ACTIONS:
        _emit_error("scanner_failed", f"invalid action {action!r}")

    if action in _STRUCTURE_ACTIONS:
        _handle_structure_action(
            category=category,
            action=action,
            pick=pick,
            into=into,
            merge_with=merge_with,
            to_name=to_name,
            new_type=new_type,
            json_mode=json_mode,
        )
        return

    action_typed: DecisionAction = cast(DecisionAction, action)
    settings = load_settings()
    profile = mine_profile(settings)
    proposals = proposals_for_walkthrough(profile)
    proposal = next((p for p in proposals if p.category == category), None)
    if proposal is None:
        _emit_error("scanner_failed", f"no proposal found for category={category!r}")

    decision = SlotDecision(
        category=category,
        action=action_typed,
        chosen_pick=pick if action_typed in ("accept", "change") else None,
        was_proposal_unchanged=(action_typed == "accept" or pick == proposal.proposed_pick),
    )
    written = (
        apply_decision(decision, proposal, on_existing=on_existing)
        if action in ("accept", "change")
        else None
    )

    if json_mode:
        _emit_json(
            {
                "mode": "confirm",
                "decision": decision.model_dump(mode="json"),
                "slot_yaml_written": str(written) if written else None,
                "structure_change": None,
            }
        )


def _handle_structure_action(
    *,
    category: str,
    action: str,
    pick: str | None,
    into: str | None,
    merge_with: str | None,
    to_name: str | None,
    new_type: str | None,
    json_mode: bool,
) -> None:
    """Apply a US4 structural action and emit the confirm payload."""

    kind = cast(StructureKind, action)
    into_list = [s.strip() for s in into.split(",")] if into else None

    # Per-action aux requirements (validators in models.py also enforce, but
    # we'd rather error early with a clear hint than emit a Pydantic stack).
    if action == "merge" and not merge_with:
        _emit_error(
            "scanner_failed", "merge requires --with <category>", hint="--with python-config"
        )
    if action == "rename" and not to_name:
        _emit_error("scanner_failed", "rename requires --to-name <new>", hint="--to-name datastore")
    if action == "add":
        if not pick or not new_type:
            _emit_error(
                "scanner_failed",
                "add requires --pick and --new-type",
                hint="--pick terraform --new-type tooling",
            )
        if new_type not in ("language", "framework", "tooling"):
            _emit_error("scanner_failed", f"invalid --new-type {new_type!r}")

    # Ensure a run state exists so append_taxonomy_edit has a target.
    run = read_bootstrap_run_state() or start_run_state()

    # For non-add actions, validate the target proposal exists.
    settings = load_settings()
    proposal = None
    if action != "add":
        profile = mine_profile(settings)
        proposals = proposals_for_walkthrough(profile)
        proposal = next((p for p in proposals if p.category == category), None)
        if proposal is None:
            _emit_error(
                "unknown_category",
                f"no proposal found for category={category!r}",
                hint="run `bis bootstrap --json --batch` to see available categories",
            )

    # Build the StructureChange.
    new_category_type = cast(CategoryType, new_type) if new_type else None
    try:
        change = StructureChange(
            kind=kind,
            category=category,
            into=into_list,
            merge_with=merge_with,
            new_name=to_name,
            new_pick=pick if action == "add" else None,
            new_category_type=new_category_type,
        )
    except Exception as exc:  # pydantic ValidationError
        _emit_error("scanner_failed", f"invalid structure change: {exc}")

    # Type narrowing for the rest of the function.
    assert proposal is not None or action == "add"

    # Apply guards specific to split / merge before persisting.
    if action == "split" and proposal is not None and into_list is None:
        suggestion = suggest_split(proposal)
        if suggestion is None:
            _emit_error(
                "split_not_supported",
                f"no heuristic split available for category={category!r}",
                hint="pass --into name1,name2,... to supply your own partition",
            )
    if action == "merge" and merge_with is not None:
        settings_for_types = load_settings()
        profile_for_types = mine_profile(settings_for_types)
        proposals_for_types = proposals_for_walkthrough(profile_for_types)
        target = next((p for p in proposals_for_types if p.category == merge_with), None)
        if target is None:
            _emit_error(
                "unknown_category",
                f"merge target category={merge_with!r} not found",
                hint="pick a category from `bis bootstrap --json --batch`",
            )
        if proposal is not None and proposal.category_type != target.category_type:
            _emit_error(
                "merge_incompatible_types",
                (
                    f"cannot merge {category!r} ({proposal.category_type}) with "
                    f"{merge_with!r} ({target.category_type})"
                ),
                hint="rename one of them first, or pick a compatible target",
            )

    # Persist the structure change.
    record_structure_change(run, change)

    # For "add", also write the slot YAML directly so the new slot is durable
    # without a follow-up accept action.
    slot_yaml_written: str | None = None
    if action == "add":
        assert change.new_pick is not None and change.new_category_type is not None
        state = SlotState(
            category=category,
            category_type=change.new_category_type,
            pick=change.new_pick,
            alternatives=[],
            evidence=EvidenceBlock(
                repo_count=0,
                most_recent=change.applied_at,
                evidence_strength=0.0,
                contributing_repos=[],
            ),
            decided_at=change.applied_at,
            history=[
                HistoryEntry(
                    action="bootstrap-add",
                    from_pick=None,
                    to_pick=change.new_pick,
                    reason="bootstrap: user added custom slot",
                    date=change.applied_at,
                )
            ],
        )
        slot_yaml_written = str(write_slot_state(state))

    decision = SlotDecision(
        category=category,
        action=cast(DecisionAction, action),
        chosen_pick=change.new_pick if action == "add" else None,
        into=into_list,
        merge_with=merge_with,
        new_name=to_name,
        new_category_type=new_category_type,
        was_proposal_unchanged=False,
    )

    if json_mode:
        _emit_json(
            {
                "mode": "confirm",
                "decision": decision.model_dump(mode="json"),
                "slot_yaml_written": slot_yaml_written,
                "structure_change": change.model_dump(mode="json", exclude_none=True),
            }
        )


# --------------------------------------------------------------------------- taxonomy-review subcommand


@bootstrap_app.command("taxonomy-review")
def bootstrap_taxonomy_review(
    json_mode: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = True,
) -> None:
    """Pre-walk overview of proposals with per-proposal split suggestions.

    Used by the bootstrap skill as the "looks good / reshape" entry point
    (FR-017).
    """

    settings = load_settings()
    profile = mine_profile(settings)
    proposals = proposals_for_walkthrough(profile)

    # Ensure a run state exists so any follow-up confirm has somewhere to
    # append taxonomy_edits.
    run = read_bootstrap_run_state() or start_run_state()

    overview: list[dict] = []
    for p in proposals:
        suggestion = suggest_split(p)
        overview.append(
            {
                "category": p.category,
                "category_type": p.category_type,
                "proposed_pick": p.proposed_pick,
                "members": [p.proposed_pick, *p.alternatives],
                "suggest_split_into": (
                    sorted(s.category for s in suggestion) if suggestion else None
                ),
            }
        )

    if json_mode:
        _emit_json(
            {
                "mode": "taxonomy-review",
                "run_id": run.run_id,
                "proposals": overview,
            }
        )


# --------------------------------------------------------------------------- restructure subcommand


@bootstrap_app.command("restructure")
def bootstrap_restructure(
    json_mode: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = True,
) -> None:
    """Enter taxonomy-edit mode against the cached proposal set (no re-mining).

    Reads the current `slots/.bootstrap.yaml` and re-emits the taxonomy-review
    overview computed from the freshly-mined profile (mining is still cheap
    when the per-repo cache is warm, FR-015). Errors with `no_prior_proposal`
    when no run state exists.
    """

    state = read_bootstrap_run_state()
    if state is None:
        _emit_error(
            "no_prior_proposal",
            "no prior bootstrap run found",
            hint="run `bis bootstrap` first to mine a proposal set",
        )

    # Re-emit the taxonomy review; the user can chain `confirm --action ...`
    # against the result.
    bootstrap_taxonomy_review(json_mode=json_mode)


# --------------------------------------------------------------------------- placeholder subcommands referenced by quickstart


@app.command("status")
def status() -> None:
    """List current slot picks (stub — full implementation in a future feature)."""

    typer.echo("bis status: not yet implemented")


if __name__ == "__main__":  # pragma: no cover
    app()
