"""Integration test: pending-dives surfaces slots needing /deep-dive (T034, US2)."""

from __future__ import annotations

import json

import pytest
import yaml
from typer.testing import CliRunner

from bis import cli as cli_mod


def _seed_slot(slots_dir, category, pick, with_readme=False, with_deep_dive=False):
    (slots_dir / f"{category}.yaml").write_text(
        yaml.safe_dump(
            {
                "category": category,
                "category_type": "framework",
                "pick": pick,
                "alternatives": [],
                "evidence": {
                    "repo_count": 1,
                    "most_recent": "2026-05-01T00:00:00+00:00",
                    "evidence_strength": 1.0,
                    "contributing_repos": [],
                },
                "decided_at": "2026-05-01T00:00:00+00:00",
                "history": [],
            }
        )
    )
    if with_readme:
        readme_dir = slots_dir / category / pick
        readme_dir.mkdir(parents=True, exist_ok=True)
        body = "# example\n"
        if with_deep_dive:
            body += "\n## Deep dive\n\nsome content\n"
        (readme_dir / "README.md").write_text(body)


@pytest.fixture
def runner():
    return CliRunner()


def test_pending_includes_slots_without_readme(tmp_slots_root, runner):
    _seed_slot(tmp_slots_root, "python-web", "fastapi", with_readme=False)
    result = runner.invoke(cli_mod.app, ["bootstrap", "pending-dives", "--json"])
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert any(p["category"] == "python-web" for p in payload["pending"])


def test_pending_excludes_slots_with_deep_dive_section(tmp_slots_root, runner):
    _seed_slot(tmp_slots_root, "python-web", "fastapi", with_readme=True, with_deep_dive=True)
    result = runner.invoke(cli_mod.app, ["bootstrap", "pending-dives", "--json"])
    payload = json.loads(result.stdout)
    assert all(p["category"] != "python-web" for p in payload["pending"])


def test_pending_includes_slots_with_readme_but_no_deep_dive(tmp_slots_root, runner):
    _seed_slot(tmp_slots_root, "python-web", "fastapi", with_readme=True, with_deep_dive=False)
    result = runner.invoke(cli_mod.app, ["bootstrap", "pending-dives", "--json"])
    payload = json.loads(result.stdout)
    assert any(p["category"] == "python-web" for p in payload["pending"])
