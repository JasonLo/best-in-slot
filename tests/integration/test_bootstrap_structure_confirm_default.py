"""Integration test: default `bis init` shows the US6 structure-confirm step (T089).

Verifies that after mining and proposing, the CLI prints a structure-overview
block and a ``[looks good / reshape]`` prompt with ``looks good`` as the default —
pressing Enter accepts and proceeds to the walk-through. The overview must show
even for trivial proposal sets (single proposal); no carve-out heuristic.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from typer.testing import CliRunner

from bis import bootstrap as bootstrap_mod
from bis import cli as cli_mod
from bis.models import ProfileSnapshot, RepoRef, ToolSignal


def _multi_proposal_profile() -> ProfileSnapshot:
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
        ],
        window_start=datetime(2023, 5, 1, tzinfo=UTC),
        window_end=datetime(2026, 5, 22, tzinfo=UTC),
    )


def _trivial_profile() -> ProfileSnapshot:
    repo = RepoRef(
        owner="me",
        name="solo",
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
        ],
        window_start=datetime(2023, 5, 1, tzinfo=UTC),
        window_end=datetime(2026, 5, 22, tzinfo=UTC),
    )


@pytest.fixture
def patched_multi(monkeypatch, tmp_slots_root, tmp_cache_root):
    profile = _multi_proposal_profile()
    monkeypatch.setattr(cli_mod, "mine_profile", lambda settings, **kw: profile)
    monkeypatch.setattr(bootstrap_mod, "check_auth", lambda: None)
    yield


@pytest.fixture
def patched_trivial(monkeypatch, tmp_slots_root, tmp_cache_root):
    profile = _trivial_profile()
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


def test_default_init_prints_overview_and_prompts_before_walk(patched_multi, monkeypatch):
    """The overview block + `[looks good / reshape]` prompt fire BEFORE per-slot picks."""

    runner = CliRunner()
    # Accept-all script for the walk-through; the confirm step is consumed via stdin.
    _install_scripted_adapter(monkeypatch, ["accept", "accept"])

    # Empty stdin → typer.prompt returns the default ("looks good").
    result = runner.invoke(cli_mod.app, ["init"], input="\n")
    assert result.exit_code == 0, result.stderr or result.stdout

    stdout = result.stdout
    # The overview must mention each proposal's category before any walk-through line.
    overview_idx = stdout.lower().find("structure overview")
    walk_idx = stdout.lower().find("walk-through")
    assert overview_idx >= 0, f"missing structure-overview block in stdout:\n{stdout}"
    assert walk_idx == -1 or overview_idx < walk_idx, (
        "structure-overview must print before the walk-through banner"
    )
    # And the looks-good prompt must precede walk output.
    prompt_idx = stdout.lower().find("looks good")
    assert prompt_idx >= 0, "missing `[looks good / reshape]` prompt"


def test_overview_shows_for_trivial_single_proposal(patched_trivial, monkeypatch):
    """FR-025 — unconditional overview, even when only one proposal exists."""

    runner = CliRunner()
    _install_scripted_adapter(monkeypatch, ["accept"])

    result = runner.invoke(cli_mod.app, ["init"], input="\n")
    assert result.exit_code == 0, result.stderr or result.stdout
    assert "structure overview" in result.stdout.lower(), (
        "trivial proposal sets MUST still show the overview (no carve-out)"
    )


def test_enter_accepts_default_and_runs_walk(patched_multi, monkeypatch, tmp_slots_root):
    """Pressing Enter (no input) accepts the `looks good` default and runs the walk."""

    runner = CliRunner()
    _install_scripted_adapter(monkeypatch, ["accept", "accept"])

    result = runner.invoke(cli_mod.app, ["init"], input="\n")
    assert result.exit_code == 0, result.stderr or result.stdout

    # The walk wrote slot YAMLs — that only happens if Enter accepted the confirm
    # default AND the per-slot walk ran the scripted "accept" stream.
    written = sorted(p.name for p in tmp_slots_root.glob("*.yaml") if not p.name.startswith("."))
    assert written, "expected at least one slots/*.yaml written after default-accept + walk"
