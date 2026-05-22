"""Integration test: end-to-end structural reshape via CLI (T054).

Fixture profile produces 4 proposals: python-tooling (lumped),
python-config, python-validation, python-terminal. The test exercises:
- split python-tooling into its 5 heuristic sub-categories
- merge python-validation into python-config
- rename databases (added below) → datastore
- drop python-terminal
- add a custom "infra" slot with "terraform"

Verifies the resulting taxonomy and that `slots/.bootstrap.yaml` contains a
replayable taxonomy_edits log.
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
    repos = [
        RepoRef(
            owner="me",
            name=f"r{i}",
            last_pushed=datetime(2026, 4, 1, tzinfo=UTC),
            is_private=False,
            is_org=False,
        )
        for i in range(3)
    ]
    pkgs = [
        # python-tooling members (post-split into 5 sub-cats)
        "uv",
        "ruff",
        "ty",
        "pytest",
        "ipykernel",
        # python-config + python-validation (merge target)
        "python-dotenv",
        "pydantic",
        # databases (rename target)
        "psycopg",
        # python-terminal (drop target)
        "typer",
    ]
    signals = []
    for repo in repos:
        for pkg in pkgs:
            signals.append(
                ToolSignal(
                    repo=repo,
                    package_name=pkg,
                    manifest_format="pyproject.toml",
                    observed_at=repo.last_pushed,
                )
            )
    return ProfileSnapshot(
        repos=repos,
        signals=signals,
        window_start=datetime(2023, 5, 1, tzinfo=UTC),
        window_end=datetime(2026, 5, 22, tzinfo=UTC),
    )


@pytest.fixture
def patched_pipeline(monkeypatch, tmp_slots_root, tmp_cache_root):
    profile = _profile()
    monkeypatch.setattr(cli_mod, "mine_profile", lambda settings, **kw: profile)
    monkeypatch.setattr(bootstrap_mod, "check_auth", lambda: None)
    yield


def _confirm(*extra: str) -> dict:
    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["bootstrap", "confirm", *extra, "--json"])
    assert result.exit_code == 0, result.stderr or result.stdout
    return json.loads(result.stdout)


# --------------------------------------------------------------------------- split


def test_split_replaces_one_proposal_with_n(patched_pipeline, tmp_slots_root):
    # build_proposals already partitions packages by heuristic, so on a fresh
    # mining pass no proposal will have splittable mixed members. Exercise
    # the user-supplied split path with --into.
    payload = _confirm(
        "--category",
        "package-manager",
        "--action",
        "split",
        "--into",
        "py-pkg-mgr,deno-pkg-mgr",
    )
    assert payload["mode"] == "confirm"
    assert payload["decision"]["action"] == "split"
    assert payload["structure_change"]["into"] == ["py-pkg-mgr", "deno-pkg-mgr"]


def test_split_persists_taxonomy_edit(patched_pipeline, tmp_slots_root):
    _confirm(
        "--category",
        "databases",
        "--action",
        "split",
        "--into",
        "sql,nosql",
    )
    state = yaml.safe_load((tmp_slots_root / ".bootstrap.yaml").read_text())
    edits = state.get("taxonomy_edits", [])
    assert any(e["kind"] == "split" and e["category"] == "databases" for e in edits), (
        f"expected split edit in {edits}"
    )


# --------------------------------------------------------------------------- merge


def test_merge_collapses_two_into_one(patched_pipeline, tmp_slots_root):
    # Both type-checker and linter-formatter are "tooling" — compatible types
    # for merge per FR-019. (python-validation is "framework", python-config
    # is "tooling" — merging them would correctly trigger
    # merge_incompatible_types.)
    payload = _confirm(
        "--category",
        "type-checker",
        "--action",
        "merge",
        "--with",
        "linter-formatter",
    )
    assert payload["decision"]["action"] == "merge"
    assert payload["structure_change"]["kind"] == "merge"

    state = yaml.safe_load((tmp_slots_root / ".bootstrap.yaml").read_text())
    edits = state["taxonomy_edits"]
    assert any(e["kind"] == "merge" and e["category"] == "type-checker" for e in edits)


def test_merge_incompatible_types_errors_clearly(patched_pipeline):
    """python-validation is 'framework'; python-config is 'tooling' — merge refused."""

    runner = CliRunner()
    result = runner.invoke(
        cli_mod.app,
        [
            "bootstrap",
            "confirm",
            "--category",
            "python-validation",
            "--action",
            "merge",
            "--with",
            "python-config",
            "--json",
        ],
    )
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["mode"] == "error"
    assert payload["error"]["code"] == "merge_incompatible_types"


# --------------------------------------------------------------------------- rename


def test_rename_changes_category_label(patched_pipeline, tmp_slots_root):
    payload = _confirm(
        "--category",
        "databases",
        "--action",
        "rename",
        "--to-name",
        "datastore",
    )
    assert payload["decision"]["new_name"] == "datastore"

    state = yaml.safe_load((tmp_slots_root / ".bootstrap.yaml").read_text())
    assert any(
        e["kind"] == "rename" and e["new_name"] == "datastore" for e in state["taxonomy_edits"]
    )


# --------------------------------------------------------------------------- drop


def test_drop_removes_proposal_from_walkthrough(patched_pipeline, tmp_slots_root):
    payload = _confirm("--category", "python-terminal", "--action", "drop")
    assert payload["decision"]["action"] == "drop"
    # drop never writes a slot YAML
    assert payload["slot_yaml_written"] is None
    assert not (tmp_slots_root / "python-terminal.yaml").exists()


# --------------------------------------------------------------------------- add


def test_add_creates_custom_slot(patched_pipeline, tmp_slots_root):
    payload = _confirm(
        "--category",
        "infra",
        "--action",
        "add",
        "--pick",
        "terraform",
        "--new-type",
        "tooling",
    )
    assert payload["decision"]["action"] == "add"
    assert payload["decision"]["chosen_pick"] == "terraform"
    # add writes the slot YAML directly (no further accept needed)
    assert (tmp_slots_root / "infra.yaml").exists()
    state = yaml.safe_load((tmp_slots_root / "infra.yaml").read_text())
    assert state["pick"] == "terraform"
    assert state["category_type"] == "tooling"


# --------------------------------------------------------------------------- combined


def test_full_reshape_flow_records_all_edits(patched_pipeline, tmp_slots_root):
    # Compatible-type merge: both tooling.
    _confirm("--category", "type-checker", "--action", "merge", "--with", "linter-formatter")
    _confirm("--category", "databases", "--action", "rename", "--to-name", "datastore")
    _confirm("--category", "python-terminal", "--action", "drop")
    _confirm(
        "--category", "infra", "--action", "add", "--pick", "terraform", "--new-type", "tooling"
    )

    state = yaml.safe_load((tmp_slots_root / ".bootstrap.yaml").read_text())
    kinds = [e["kind"] for e in state["taxonomy_edits"]]
    assert "merge" in kinds
    assert "rename" in kinds
    assert "drop" in kinds
    assert "add" in kinds
