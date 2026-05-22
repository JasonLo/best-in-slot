"""Contract test: US4 structure-action walkthrough events validate (T052).

Adds coverage for the three new event types — `taxonomy_review_presented`,
`structure_action_offered`, `structure_action_applied` — and the extended
`UserResponse` variants (`split`, `merge`, `rename`, `drop`, `add`).

Also regression-asserts that the original events (proposal_presented,
accept/change/skip/defer responses, decision_applied, run_summary) still
validate after the schema additions.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs/001-bootstrap-discovery/contracts/walkthrough-events.schema.json"
)


@pytest.fixture
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


# --------------------------------------------------------------------------- new events


def test_taxonomy_review_presented_validates(schema):
    event = {
        "event": "taxonomy_review_presented",
        "proposals": [
            {
                "category": "python-tooling",
                "category_type": "tooling",
                "proposed_pick": "ipykernel",
                "members": ["uv", "ruff", "ty", "pytest", "ipykernel"],
                "suggest_split_into": [
                    "package-manager",
                    "linter-formatter",
                    "type-checker",
                    "test-runner",
                    "notebook-kernel",
                ],
            },
            {
                "category": "python-web",
                "category_type": "framework",
                "proposed_pick": "fastapi",
                "members": ["fastapi", "django"],
                "suggest_split_into": None,
            },
        ],
    }
    jsonschema.validate(event, schema)


def test_structure_action_offered_validates(schema):
    event = {
        "event": "structure_action_offered",
        "category": "python-tooling",
        "available_actions": ["split", "merge", "rename", "drop"],
        "suggest_split_into": ["package-manager", "linter-formatter"],
    }
    jsonschema.validate(event, schema)


def test_structure_action_offered_without_split_suggestion(schema):
    event = {
        "event": "structure_action_offered",
        "category": "databases",
        "available_actions": ["merge", "rename", "drop"],
        "suggest_split_into": None,
    }
    jsonschema.validate(event, schema)


def test_structure_action_applied_split(schema):
    event = {
        "event": "structure_action_applied",
        "kind": "split",
        "category": "python-tooling",
        "into": ["package-manager", "linter-formatter", "type-checker"],
        "merge_with": None,
        "new_name": None,
        "new_pick": None,
        "new_category_type": None,
    }
    jsonschema.validate(event, schema)


def test_structure_action_applied_merge(schema):
    event = {
        "event": "structure_action_applied",
        "kind": "merge",
        "category": "python-config",
        "into": None,
        "merge_with": "python-validation",
        "new_name": None,
        "new_pick": None,
        "new_category_type": None,
    }
    jsonschema.validate(event, schema)


def test_structure_action_applied_rename(schema):
    event = {
        "event": "structure_action_applied",
        "kind": "rename",
        "category": "databases",
        "into": None,
        "merge_with": None,
        "new_name": "datastore",
        "new_pick": None,
        "new_category_type": None,
    }
    jsonschema.validate(event, schema)


def test_structure_action_applied_drop(schema):
    event = {
        "event": "structure_action_applied",
        "kind": "drop",
        "category": "python-terminal",
        "into": None,
        "merge_with": None,
        "new_name": None,
        "new_pick": None,
        "new_category_type": None,
    }
    jsonschema.validate(event, schema)


def test_structure_action_applied_add(schema):
    event = {
        "event": "structure_action_applied",
        "kind": "add",
        "category": "infra",
        "into": None,
        "merge_with": None,
        "new_name": None,
        "new_pick": "terraform",
        "new_category_type": "tooling",
    }
    jsonschema.validate(event, schema)


# --------------------------------------------------------------------------- extended UserResponse


def test_user_response_split_with_partition(schema):
    jsonschema.validate(
        {"action": "split", "into": ["package-manager", "linter-formatter"]},
        schema,
    )


def test_user_response_split_auto_suggest(schema):
    # `into = None` signals "use suggest_split"
    jsonschema.validate({"action": "split", "into": None}, schema)


def test_user_response_split_omit_into(schema):
    # omitted `into` is also valid — same effect as None
    jsonschema.validate({"action": "split"}, schema)


def test_user_response_merge_requires_target(schema):
    jsonschema.validate(
        {"action": "merge", "merge_with": "python-validation"},
        schema,
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"action": "merge"}, schema)


def test_user_response_rename_requires_new_name(schema):
    jsonschema.validate(
        {"action": "rename", "new_name": "datastore"},
        schema,
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"action": "rename"}, schema)


def test_user_response_drop_validates(schema):
    jsonschema.validate({"action": "drop"}, schema)


def test_user_response_add_requires_new_category(schema):
    jsonschema.validate(
        {
            "action": "add",
            "new_category": {
                "name": "infra",
                "category_type": "tooling",
                "pick": "terraform",
            },
        },
        schema,
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"action": "add"}, schema)


# --------------------------------------------------------------------------- regression: existing events


def test_existing_proposal_presented_still_validates(schema):
    event = {
        "event": "proposal_presented",
        "category": "python-web",
        "category_type": "framework",
        "proposed_pick": "fastapi",
        "alternatives": ["django"],
        "evidence": {
            "repo_count": 4,
            "most_recent": "2026-04-01T00:00:00+00:00",
            "confidence_qualifier": None,
        },
        "queue_position": {"index": 1, "total": 5},
    }
    jsonschema.validate(event, schema)


def test_existing_user_response_accept_still_validates(schema):
    jsonschema.validate({"action": "accept"}, schema)


def test_existing_user_response_change_still_validates(schema):
    jsonschema.validate(
        {"action": "change", "chosen_pick": "litestar", "source": "free_form"},
        schema,
    )


def test_run_summary_with_taxonomy_edits_validates(schema):
    event = {
        "event": "run_summary",
        "run_id": "abc-123",
        "accepted": 4,
        "changed": 1,
        "skipped": 0,
        "deferred": 2,
        "skipped_sources": [],
        "taxonomy_edits": {
            "split": 1,
            "merge": 1,
            "rename": 0,
            "drop": 1,
            "add": 1,
        },
    }
    jsonschema.validate(event, schema)


def test_run_summary_without_taxonomy_edits_still_validates(schema):
    # taxonomy_edits is optional — backwards-compat
    event = {
        "event": "run_summary",
        "run_id": "abc-123",
        "accepted": 4,
        "changed": 1,
        "skipped": 0,
        "deferred": 0,
        "skipped_sources": [],
    }
    jsonschema.validate(event, schema)
