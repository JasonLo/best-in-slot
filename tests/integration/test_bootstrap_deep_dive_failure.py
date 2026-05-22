"""Integration test: a failed deep-dive on one slot doesn't poison the others (T035, FR-011).

The bootstrap CLI doesn't *invoke* /deep-dive — the skill does. What the CLI
owns is the `pending-dives` subcommand and the slot YAML it reads to decide
"dived vs not." This test pins the contract from the CLI's side:

  - If slot A's deep-dive succeeded (README.md with `## Deep dive`), A is not
    pending.
  - If slot B's deep-dive failed (no README, or README without the marker), B
    remains pending — independently of A's status.

That's the foundation the skill relies on when it surfaces "still need a dive
on B" after a failure.

The walk-through-event schema additionally permits a `deep_dive_failures` block
on the RunSummary event — exercised in `tests/contract/test_walkthrough_events.py`.
"""

from __future__ import annotations

import json

import pytest
import yaml
from typer.testing import CliRunner

from bis import cli as cli_mod


def _seed_slot(slots_dir, category, pick, *, readme_body: str | None) -> None:
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
    if readme_body is not None:
        readme_dir = slots_dir / category / pick
        readme_dir.mkdir(parents=True, exist_ok=True)
        (readme_dir / "README.md").write_text(readme_body)


@pytest.fixture
def runner():
    return CliRunner()


def test_failed_dive_keeps_slot_in_pending_list(tmp_slots_root, runner):
    # Slot A: dive succeeded.
    _seed_slot(
        tmp_slots_root, "python-web", "fastapi", readme_body="# fastapi\n\n## Deep dive\n\nok\n"
    )
    # Slot B: dive failed — we simulate by leaving the README missing entirely.
    _seed_slot(tmp_slots_root, "python-data", "pandas", readme_body=None)
    # Slot C: dive failed differently — README exists but no `## Deep dive`.
    _seed_slot(tmp_slots_root, "test-runner", "pytest", readme_body="# pytest\n\nbody\n")

    result = runner.invoke(cli_mod.app, ["bootstrap", "pending-dives", "--json"])
    assert result.exit_code == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    pending_categories = {p["category"] for p in payload["pending"]}

    assert "python-web" not in pending_categories, "succeeded dive should not stay pending"
    assert "python-data" in pending_categories, "missing-README failure must stay pending"
    assert "test-runner" in pending_categories, "missing-section failure must stay pending"


def test_pending_dives_does_not_abort_on_any_one_slot(tmp_slots_root, runner):
    """Even with a malformed-looking slot (no README), the subcommand returns the rest."""

    _seed_slot(tmp_slots_root, "python-web", "fastapi", readme_body=None)
    _seed_slot(tmp_slots_root, "python-data", "pandas", readme_body=None)
    _seed_slot(tmp_slots_root, "test-runner", "pytest", readme_body=None)

    result = runner.invoke(cli_mod.app, ["bootstrap", "pending-dives", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert len(payload["pending"]) == 3
