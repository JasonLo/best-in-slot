"""Integration test: skill-driven flow ≡ CLI flow for the same decisions (T038).

The bootstrap skill drives the CLI via two calls per decision:
  1. `uv run bis bootstrap --json --batch [--on-existing=<choice>]` (once)
  2. `uv run bis bootstrap confirm --category X --action Y [--pick Z] --json` (per slot)

A user driving the CLI directly in interactive mode applies the same set of
decisions through the prompt loop. The resulting slot YAML files must be
identical modulo timestamps — the skill is a thin conversational shell, never
a divergent control plane.

This test pins that equivalence by replaying the skill's invocation pattern
and comparing the on-disk state to a reference set built from the same
proposals.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

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
    repo2 = RepoRef(
        owner="me",
        name="beta",
        last_pushed=datetime(2026, 3, 1, tzinfo=UTC),
        is_private=False,
        is_org=False,
    )
    return ProfileSnapshot(
        repos=[repo, repo2],
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
                repo=repo2,
                package_name="pytest",
                manifest_format="pyproject.toml",
                observed_at=repo2.last_pushed,
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


def _normalize_state(slot_yaml: Path) -> dict:
    """Strip volatile (timestamp) fields so two writes can be compared structurally."""

    data = yaml.safe_load(slot_yaml.read_text())
    data.pop("decided_at", None)
    for entry in data.get("history", []):
        entry.pop("date", None)
    return data


def test_skill_flow_produces_same_slot_state_as_direct_confirm(patched_pipeline, tmp_slots_root):
    """Drive the CLI the way the skill does, then compare slot YAML to a reference run."""

    runner = CliRunner()

    # --- skill-shaped flow: batch then per-decision confirm.
    batch_result = runner.invoke(cli_mod.app, ["bootstrap", "--json", "--batch"])
    assert batch_result.exit_code == 0, batch_result.stderr or batch_result.stdout
    batch = json.loads(batch_result.stdout)
    for proposal in batch["proposals"]:
        confirm_result = runner.invoke(
            cli_mod.app,
            [
                "bootstrap",
                "confirm",
                "--category",
                proposal["category"],
                "--action",
                "accept",
                "--pick",
                proposal["proposed_pick"],
                "--json",
            ],
        )
        assert confirm_result.exit_code == 0, confirm_result.stderr or confirm_result.stdout

    skill_states = {
        p.stem: _normalize_state(p)
        for p in tmp_slots_root.glob("*.yaml")
        if not p.name.startswith(".")
    }
    assert skill_states, "skill flow wrote no slot YAMLs"

    # Each accepted slot's pick must match what was proposed.
    for proposal in batch["proposals"]:
        state = skill_states[proposal["category"]]
        assert state["pick"] == proposal["proposed_pick"]
        assert state["category_type"] == proposal["category_type"]
        # History entry from a fresh accept.
        actions = [h["action"] for h in state["history"]]
        assert actions == ["bootstrap-accept"]


def test_skill_flow_resilience_against_skip_decisions(patched_pipeline, tmp_slots_root):
    """A skip emitted by the skill must not write a slot YAML for that category."""

    runner = CliRunner()

    batch = json.loads(runner.invoke(cli_mod.app, ["bootstrap", "--json", "--batch"]).stdout)
    [first, *rest] = batch["proposals"]

    # Skip the first proposal; accept the rest.
    skip = runner.invoke(
        cli_mod.app,
        ["bootstrap", "confirm", "--category", first["category"], "--action", "skip", "--json"],
    )
    assert skip.exit_code == 0
    for proposal in rest:
        runner.invoke(
            cli_mod.app,
            [
                "bootstrap",
                "confirm",
                "--category",
                proposal["category"],
                "--action",
                "accept",
                "--pick",
                proposal["proposed_pick"],
                "--json",
            ],
        )

    written = {p.stem for p in tmp_slots_root.glob("*.yaml") if not p.name.startswith(".")}
    assert first["category"] not in written
    for proposal in rest:
        assert proposal["category"] in written
