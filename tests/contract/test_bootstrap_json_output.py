"""Contract test: `bis init --json --batch` output matches the JSON Schema (T011)."""

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
def patched_pipeline(monkeypatch, tmp_slots_root):
    """Replace the network layer with an in-memory ProfileSnapshot."""

    repo = RepoRef(
        owner="me",
        name="proj",
        last_pushed=datetime(2026, 4, 1, tzinfo=UTC),
        is_private=False,
        is_org=False,
    )
    sig = ToolSignal(
        repo=repo,
        package_name="fastapi",
        manifest_format="pyproject.toml",
        observed_at=repo.last_pushed,
    )
    sig2 = ToolSignal(
        repo=repo,
        package_name="pandas",
        manifest_format="pyproject.toml",
        observed_at=repo.last_pushed,
    )
    profile = ProfileSnapshot(
        repos=[repo],
        signals=[sig, sig2],
        window_start=datetime(2023, 5, 1, tzinfo=UTC),
        window_end=datetime(2026, 5, 22, tzinfo=UTC),
    )

    def _fake_mine(settings, **kwargs):  # noqa: ANN001
        return profile

    monkeypatch.setattr(cli_mod, "mine_profile", _fake_mine)
    monkeypatch.setattr(bootstrap_mod, "check_auth", lambda: None)
    yield


def test_batch_output_matches_schema(schema, patched_pipeline, tmp_slots_root):
    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["init", "--json", "--batch"])
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["mode"] == "batch"
    jsonschema.validate(payload, schema)


def test_existing_state_error_envelope_matches_schema(
    schema, patched_pipeline, tmp_slots_root, monkeypatch
):
    # Plant an existing slot YAML so the existing-state guard fires.
    (tmp_slots_root / "python-web.yaml").write_text(
        "category: python-web\ncategory_type: framework\npick: fastapi\nalternatives: []\nevidence: {repo_count: 1, most_recent: '2026-05-01T00:00:00+00:00', evidence_strength: 1.0, contributing_repos: []}\ndecided_at: '2026-05-01T00:00:00+00:00'\nhistory: []\n"
    )
    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["init", "--json", "--batch"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["mode"] == "error"
    assert payload["error"]["code"] == "existing_state_unresolved"
    jsonschema.validate(payload, schema)
