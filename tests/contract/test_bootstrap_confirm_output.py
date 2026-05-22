"""Contract test: `bis bootstrap confirm --json` output for each action (T012).

Each action (accept / change / skip / defer) must produce a payload that
validates against the `bis bootstrap confirm` branch of
`specs/001-bootstrap-discovery/contracts/bootstrap.schema.json`.
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
    """Stand in a deterministic two-package profile for the confirm flow."""

    repo = RepoRef(
        owner="me",
        name="alpha",
        last_pushed=datetime(2026, 4, 1, tzinfo=UTC),
        is_private=False,
        is_org=False,
    )
    profile = ProfileSnapshot(
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
                package_name="httpx",
                manifest_format="pyproject.toml",
                observed_at=repo.last_pushed,
            ),
        ],
        window_start=datetime(2023, 5, 1, tzinfo=UTC),
        window_end=datetime(2026, 5, 22, tzinfo=UTC),
    )
    monkeypatch.setattr(cli_mod, "mine_profile", lambda settings, **kw: profile)
    monkeypatch.setattr(bootstrap_mod, "check_auth", lambda: None)
    yield


def _invoke_confirm(*extra: str) -> dict:
    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["bootstrap", "confirm", *extra, "--json"])
    assert result.exit_code == 0, result.stderr or result.stdout
    return json.loads(result.stdout)


def test_confirm_accept_matches_schema(schema, patched_pipeline):
    payload = _invoke_confirm("--category", "python-web", "--action", "accept", "--pick", "fastapi")
    jsonschema.validate(payload, schema)
    assert payload["mode"] == "confirm"
    assert payload["decision"]["action"] == "accept"
    assert payload["decision"]["chosen_pick"] == "fastapi"
    assert payload["slot_yaml_written"]


def test_confirm_change_matches_schema(schema, patched_pipeline):
    payload = _invoke_confirm("--category", "python-web", "--action", "change", "--pick", "django")
    jsonschema.validate(payload, schema)
    assert payload["decision"]["action"] == "change"
    assert payload["decision"]["chosen_pick"] == "django"
    assert payload["decision"]["was_proposal_unchanged"] is False


def test_confirm_skip_matches_schema(schema, patched_pipeline):
    payload = _invoke_confirm("--category", "python-web", "--action", "skip")
    jsonschema.validate(payload, schema)
    assert payload["decision"]["action"] == "skip"
    assert payload["decision"]["chosen_pick"] is None
    assert payload["slot_yaml_written"] is None


def test_confirm_defer_matches_schema(schema, patched_pipeline):
    payload = _invoke_confirm("--category", "python-web", "--action", "defer")
    jsonschema.validate(payload, schema)
    assert payload["decision"]["action"] == "defer"
    assert payload["decision"]["chosen_pick"] is None
    assert payload["slot_yaml_written"] is None
