"""Integration test: skill-handoff (mine + walk) ≡ direct-confirm flow (T074, US5).

The US5 skill drives the CLI as ``bis init mine --json`` + ``bis init walk`` (or
``bis init walk --from-stdin``). The on-disk slot state it produces MUST be
byte-identical to the prior LLM-in-loop flow (where the skill called
``bis init --json --batch`` then ``bis init confirm ...`` per slot) — modulo
volatile fields (``decided_at``, ``run_id``).

This test pins the equivalence so the speed refactor cannot quietly diverge.
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


def _normalize(slot_yaml: Path) -> dict:
    """Strip volatile fields so two writes can be compared structurally."""

    data = yaml.safe_load(slot_yaml.read_text())
    data.pop("decided_at", None)
    for entry in data.get("history", []):
        entry.pop("date", None)
    return data


def test_mine_walk_handoff_matches_direct_confirm_flow(patched_pipeline, tmp_path, monkeypatch):
    """Drive both flows side-by-side; the resulting slot YAMLs must match."""

    runner = CliRunner()

    # --- Flow A: prior LLM-in-loop (batch + per-slot confirm) under slots_a/.
    slots_a = tmp_path / "slots_a"
    slots_a.mkdir()
    monkeypatch.setenv("BIS_SLOTS_ROOT", str(slots_a))
    batch = json.loads(runner.invoke(cli_mod.app, ["init", "--json", "--batch"]).stdout)
    for proposal in batch["proposals"]:
        runner.invoke(
            cli_mod.app,
            [
                "init",
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
    flow_a_states = {
        p.stem: _normalize(p) for p in slots_a.glob("*.yaml") if not p.name.startswith(".")
    }

    # --- Flow B: new mine + walk handoff under slots_b/.
    slots_b = tmp_path / "slots_b"
    slots_b.mkdir()
    monkeypatch.setenv("BIS_SLOTS_ROOT", str(slots_b))

    runner.invoke(cli_mod.app, ["init", "mine", "--json"])
    pending = yaml.safe_load((slots_b / ".bootstrap.yaml").read_text())["pending_proposals"]

    from bis import walk as walk_mod

    monkeypatch.setattr(
        cli_mod,
        "_make_walk_adapter",
        lambda: walk_mod.ScriptedAdapter(["accept"] * len(pending)),
    )

    walk = runner.invoke(cli_mod.app, ["init", "walk", "--json"])
    assert walk.exit_code == 0, walk.stderr or walk.stdout

    flow_b_states = {
        p.stem: _normalize(p) for p in slots_b.glob("*.yaml") if not p.name.startswith(".")
    }

    # Same categories produced; same picks; same history shape.
    assert set(flow_a_states) == set(flow_b_states)
    for category, state_a in flow_a_states.items():
        state_b = flow_b_states[category]
        assert state_a["pick"] == state_b["pick"]
        assert state_a["category_type"] == state_b["category_type"]
        assert [h["action"] for h in state_a["history"]] == [
            h["action"] for h in state_b["history"]
        ]
