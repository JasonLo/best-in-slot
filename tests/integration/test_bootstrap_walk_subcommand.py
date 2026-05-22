"""Integration test: ``bis init walk`` drives the persisted proposals (T073, US5).

End-to-end fast-path:

  1. ``bis init mine --json`` persists ``pending_proposals`` into ``slots/.bootstrap.yaml``.
  2. ``bis init walk`` reads them, drives the per-slot decisions through an injected
     ``ScriptedAdapter`` (no real TTY), writes ``slots/{category}.yaml`` for accepts/changes,
     clears ``pending_proposals``, and emits a JSON summary.

Tests pin both the happy path and a no-pending-proposals error envelope.
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


def test_walk_consumes_pending_and_writes_slot_yamls(patched_pipeline, tmp_slots_root, monkeypatch):
    runner = CliRunner()

    mine = runner.invoke(cli_mod.app, ["init", "mine", "--json"])
    assert mine.exit_code == 0
    mine_payload = json.loads(mine.stdout)
    pending = mine_payload["proposals"]
    assert pending, "mine must produce at least one proposal"

    _install_scripted_adapter(monkeypatch, ["accept"] * len(pending))

    walk = runner.invoke(cli_mod.app, ["init", "walk", "--json"])
    assert walk.exit_code == 0, walk.stderr or walk.stdout
    payload = json.loads(walk.stdout)

    assert payload["mode"] == "walk"
    assert payload["decisions_count"]["accept"] == len(pending)
    assert payload["decisions_count"]["change"] == 0
    assert payload["decisions_count"]["skip"] == 0
    assert payload["decisions_count"]["defer"] == 0
    assert len(payload["slot_yamls_written"]) == len(pending)

    # One YAML per accepted proposal.
    written = {p.stem for p in tmp_slots_root.glob("*.yaml") if not p.name.startswith(".")}
    assert {p["category"] for p in pending} == written


def test_walk_clears_pending_proposals_after_completion(
    patched_pipeline, tmp_slots_root, monkeypatch
):
    runner = CliRunner()
    runner.invoke(cli_mod.app, ["init", "mine", "--json"])
    pre = yaml.safe_load((tmp_slots_root / ".bootstrap.yaml").read_text())
    assert pre.get("pending_proposals"), "pre-walk should have pending_proposals"

    _install_scripted_adapter(monkeypatch, ["accept"] * len(pre["pending_proposals"]))

    runner.invoke(cli_mod.app, ["init", "walk", "--json"])
    post = yaml.safe_load((tmp_slots_root / ".bootstrap.yaml").read_text())
    assert post.get("pending_proposals") in (None, []), (
        "walk must clear pending_proposals on completion"
    )


def test_walk_with_no_pending_proposals_errors(patched_pipeline, tmp_slots_root, monkeypatch):
    """Calling ``bis init walk`` without a prior mine emits a clean error envelope."""

    runner = CliRunner()
    _install_scripted_adapter(monkeypatch, [])

    # No `bis init mine` first → no pending proposals.
    walk = runner.invoke(cli_mod.app, ["init", "walk", "--json"])

    assert walk.exit_code != 0
    err = json.loads(walk.stdout)
    assert err["mode"] == "error"
    assert err["error"]["code"] == "no_pending_proposals"


def test_walk_handles_change_skip_defer_actions(patched_pipeline, tmp_slots_root, monkeypatch):
    runner = CliRunner()
    mine = runner.invoke(cli_mod.app, ["init", "mine", "--json"])
    pending = json.loads(mine.stdout)["proposals"]
    assert len(pending) >= 2, "fixture must produce ≥2 proposals to exercise mixed actions"

    # Build a script: change the first, skip the second, accept the rest.
    first_alternative = (
        pending[0]["alternatives"][0] if pending[0]["alternatives"] else "custom-pick"
    )
    script: list[str] = [f"change:{first_alternative}", "skip"] + ["accept"] * (len(pending) - 2)
    _install_scripted_adapter(monkeypatch, script)

    walk = runner.invoke(cli_mod.app, ["init", "walk", "--json"])
    assert walk.exit_code == 0, walk.stderr or walk.stdout
    payload = json.loads(walk.stdout)

    assert payload["decisions_count"]["change"] == 1
    assert payload["decisions_count"]["skip"] == 1
    assert payload["decisions_count"]["accept"] == len(pending) - 2

    # Skipped category gets no YAML.
    written = {p.stem for p in tmp_slots_root.glob("*.yaml") if not p.name.startswith(".")}
    assert pending[1]["category"] not in written

    # Changed category persists with the new pick.
    changed_state = yaml.safe_load((tmp_slots_root / f"{pending[0]['category']}.yaml").read_text())
    assert changed_state["pick"] == first_alternative
