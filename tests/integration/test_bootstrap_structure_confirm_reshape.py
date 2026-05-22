"""Integration test: US6 reshape inner loop + `bis init walk --skip-confirm` (T090).

Verifies that:

  1. Entering ``reshape`` opens a single inner loop accepting repeated structural
     actions; each edit gets ``applied_at_phase == "confirm"`` and exiting requires
     an explicit ``done`` action. Only one trip through ``[looks good / reshape]``
     is needed.
  2. ``bis init walk --skip-confirm`` bypasses the confirm step entirely
     (skill-flow parity — FR-024 byte-identical-result invariant).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
import yaml
from typer.testing import CliRunner

from bis import bootstrap as bootstrap_mod
from bis import cli as cli_mod
from bis.models import ProfileSnapshot, RepoRef, ToolSignal


def _profile() -> ProfileSnapshot:
    repo = RepoRef(
        owner="me",
        name="alpha",
        last_pushed=datetime(2026, 4, 1, tzinfo=UTC),
        is_private=False,
        is_org=False,
    )
    return ProfileSnapshot(
        repos=[repo],
        signals=[
            ToolSignal(
                repo=repo,
                package_name="fastapi",
                manifest_format="pyproject.toml",
                observed_at=repo.last_pushed,
            ),
            ToolSignal(
                repo=repo,
                package_name="ruff",
                manifest_format="pyproject.toml",
                observed_at=repo.last_pushed,
            ),
            ToolSignal(
                repo=repo,
                package_name="uv",
                manifest_format="pyproject.toml",
                observed_at=repo.last_pushed,
            ),
        ],
        window_start=datetime(2023, 5, 1, tzinfo=UTC),
        window_end=datetime(2026, 5, 22, tzinfo=UTC),
    )


@pytest.fixture
def patched_pipeline(monkeypatch, tmp_slots_root, tmp_cache_root):
    profile = _profile()
    monkeypatch.setattr(cli_mod, "mine_profile", lambda settings, **kw: profile)
    monkeypatch.setattr(bootstrap_mod, "check_auth", lambda: None)
    yield


def _install_scripted_adapter(monkeypatch, answers):
    from bis import walk as walk_mod

    monkeypatch.setattr(
        cli_mod,
        "_make_walk_adapter",
        lambda: walk_mod.ScriptedAdapter(answers),
    )


def test_reshape_inner_loop_accepts_multiple_edits_in_one_session(
    patched_pipeline, tmp_slots_root, monkeypatch
):
    """Two structural edits in a single reshape session — both tagged confirm-phase."""

    runner = CliRunner()
    # After reshape exits, we need adapter answers for whatever proposals remain.
    # Be generous: 10 accepts should cover any rebuild.
    _install_scripted_adapter(monkeypatch, ["accept"] * 10)

    # Fixture produces categories: python-web (fastapi), linter-formatter (ruff),
    # package-manager (uv). Script applies rename + drop, then done.
    stdin = (
        "\n".join(
            [
                "reshape",  # enter reshape from [looks good / reshape]
                "rename",  # action
                "python-web",  # target category (exists in fixture)
                "web-framework",  # new name
                "drop",  # next action — same inner loop
                "linter-formatter",  # target category to drop (exists in fixture)
                "done",  # exit reshape loop
                "",  # any trailing prompt
            ]
        )
        + "\n"
    )

    result = runner.invoke(cli_mod.app, ["init"], input=stdin)
    assert result.exit_code == 0, result.stderr or result.stdout

    # Inspect the run-state taxonomy_edits.
    bootstrap_yaml = tmp_slots_root / ".bootstrap.yaml"
    assert bootstrap_yaml.exists(), "bootstrap run state should be persisted"
    state = yaml.safe_load(bootstrap_yaml.read_text())
    edits = state.get("taxonomy_edits", [])
    assert len(edits) >= 2, f"expected ≥2 taxonomy_edits, got {len(edits)}: {edits!r}"

    confirm_phase_edits = [e for e in edits if e.get("applied_at_phase") == "confirm"]
    assert len(confirm_phase_edits) >= 2, (
        f"all reshape-phase edits must be tagged applied_at_phase='confirm'; "
        f"got phases: {[e.get('applied_at_phase') for e in edits]!r}"
    )


def test_walk_skip_confirm_bypasses_overview_prompt(patched_pipeline, tmp_slots_root, monkeypatch):
    """`bis init walk --skip-confirm` (skill flow) sees no structure-confirm prompt."""

    runner = CliRunner()

    # First, populate pending_proposals via `bis init mine`.
    mine = runner.invoke(cli_mod.app, ["init", "mine", "--json"])
    assert mine.exit_code == 0, mine.stderr or mine.stdout
    pending = json.loads(mine.stdout)["proposals"]
    assert pending, "fixture must produce ≥1 proposal"

    _install_scripted_adapter(monkeypatch, ["accept"] * len(pending))

    # No stdin input — if the confirm prompt fires, typer.prompt would block / fail.
    walk = runner.invoke(cli_mod.app, ["init", "walk", "--skip-confirm", "--json"])
    assert walk.exit_code == 0, walk.stderr or walk.stdout

    # The bypassed step leaves NO "looks good" prompt text in stdout.
    assert "looks good" not in walk.stdout.lower(), (
        "--skip-confirm must suppress the structure-confirm prompt"
    )
    payload = json.loads(walk.stdout)
    assert payload["mode"] == "walk"


def test_walk_without_skip_confirm_shows_prompt(patched_pipeline, tmp_slots_root, monkeypatch):
    """Default `bis init walk` (no flag) — confirm step DOES fire (FR-025 parity)."""

    runner = CliRunner()
    mine = runner.invoke(cli_mod.app, ["init", "mine", "--json"])
    assert mine.exit_code == 0
    pending = json.loads(mine.stdout)["proposals"]

    _install_scripted_adapter(monkeypatch, ["accept"] * len(pending))

    # Default-accept the confirm step (Enter), then the walk runs.
    walk = runner.invoke(cli_mod.app, ["init", "walk", "--json"], input="\n")
    assert walk.exit_code == 0, walk.stderr or walk.stdout
    assert "looks good" in walk.stdout.lower(), (
        "bis init walk (no --skip-confirm) MUST surface the structure-confirm prompt"
    )
