"""Contract test: `bis init confirm --action {split|merge|rename|drop|add}` (T053).

Each structure action must produce a payload that validates against the
extended `bis init confirm` branch of bootstrap.schema.json, including
the per-action aux fields (`into`, `merge_with`, `new_name`, `new_category_type`).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import jsonschema
import pytest
from typer.testing import CliRunner

from bis import bootstrap as bootstrap_mod
from bis import cli as cli_mod
from bis.models import ProfileSnapshot, RepoRef, ToolSignal

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs/001-bootstrap-discovery/contracts/bootstrap.schema.json"
)


@pytest.fixture
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


@pytest.fixture
def patched_pipeline(monkeypatch, tmp_slots_root, tmp_cache_root):
    """A profile with python-tooling members that suggest_split can partition."""

    repo = RepoRef(
        owner="me",
        name="alpha",
        last_pushed=datetime(2026, 4, 1, tzinfo=UTC),
        is_private=False,
        is_org=False,
    )
    signals = [
        ToolSignal(
            repo=repo,
            package_name=name,
            manifest_format="pyproject.toml",
            observed_at=repo.last_pushed,
        )
        for name in ("uv", "ruff", "ty", "pytest", "ipykernel", "fastapi")
    ]
    profile = ProfileSnapshot(
        repos=[repo],
        signals=signals,
        window_start=datetime(2023, 5, 1, tzinfo=UTC),
        window_end=datetime(2026, 5, 22, tzinfo=UTC),
    )
    monkeypatch.setattr(cli_mod, "mine_profile", lambda settings, **kw: profile)
    monkeypatch.setattr(bootstrap_mod, "check_auth", lambda: None)
    yield


def _invoke_confirm(*extra: str) -> dict:
    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["init", "confirm", *extra, "--json"])
    assert result.exit_code == 0, result.stderr or result.stdout
    return json.loads(result.stdout)


def test_confirm_split_matches_schema(schema, patched_pipeline):
    # Build_proposals already partitions by heuristic, so suggest_split
    # rarely fires on a freshly-mined proposal. Exercise the user-supplied
    # split path with --into.
    payload = _invoke_confirm(
        "--category",
        "package-manager",
        "--action",
        "split",
        "--into",
        "py-pkg-mgr,deno-pkg-mgr",
    )
    jsonschema.validate(payload, schema)
    assert payload["mode"] == "confirm"
    assert payload["decision"]["action"] == "split"
    assert payload["decision"]["chosen_pick"] is None
    assert payload["structure_change"]["kind"] == "split"


def test_confirm_split_without_heuristic_errors_clearly(schema, patched_pipeline):
    """When suggest_split can't partition AND no --into is given,
    the CLI emits split_not_supported."""

    runner = CliRunner()
    result = runner.invoke(
        cli_mod.app,
        ["init", "confirm", "--category", "package-manager", "--action", "split", "--json"],
    )
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    jsonschema.validate(payload, schema)
    assert payload["mode"] == "error"
    assert payload["error"]["code"] == "split_not_supported"


def test_confirm_merge_matches_schema(schema, patched_pipeline):
    payload = _invoke_confirm(
        "--category",
        "package-manager",
        "--action",
        "merge",
        "--with",
        "linter-formatter",
    )
    jsonschema.validate(payload, schema)
    assert payload["decision"]["action"] == "merge"
    assert payload["decision"]["merge_with"] == "linter-formatter"
    assert payload["structure_change"]["kind"] == "merge"
    assert payload["structure_change"]["merge_with"] == "linter-formatter"


def test_confirm_rename_matches_schema(schema, patched_pipeline):
    payload = _invoke_confirm(
        "--category",
        "package-manager",
        "--action",
        "rename",
        "--to-name",
        "py-pkg-mgr",
    )
    jsonschema.validate(payload, schema)
    assert payload["decision"]["action"] == "rename"
    assert payload["decision"]["new_name"] == "py-pkg-mgr"
    assert payload["structure_change"]["new_name"] == "py-pkg-mgr"


def test_confirm_drop_matches_schema(schema, patched_pipeline):
    payload = _invoke_confirm(
        "--category",
        "notebook-kernel",
        "--action",
        "drop",
    )
    jsonschema.validate(payload, schema)
    assert payload["decision"]["action"] == "drop"
    assert payload["decision"]["chosen_pick"] is None
    assert payload["structure_change"]["kind"] == "drop"


def test_confirm_add_matches_schema(schema, patched_pipeline):
    payload = _invoke_confirm(
        "--category",
        "infra",
        "--action",
        "add",
        "--pick",
        "terraform",
        "--new-type",
        "tooling",
    )
    jsonschema.validate(payload, schema)
    assert payload["decision"]["action"] == "add"
    assert payload["decision"]["chosen_pick"] == "terraform"
    assert payload["decision"]["new_category_type"] == "tooling"
    assert payload["structure_change"]["kind"] == "add"


def test_existing_accept_still_matches_schema(schema, patched_pipeline):
    """Regression: the pre-US4 actions still validate."""

    payload = _invoke_confirm(
        "--category",
        "python-web",
        "--action",
        "accept",
        "--pick",
        "fastapi",
    )
    jsonschema.validate(payload, schema)
    assert payload["decision"]["action"] == "accept"
    assert payload["decision"]["chosen_pick"] == "fastapi"
