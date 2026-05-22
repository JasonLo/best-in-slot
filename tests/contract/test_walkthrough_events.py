"""Contract test: walk-through event payloads validate against the event schema (T013).

These events are rendered as conversation turns by the bootstrap skill (not
emitted as JSON over the wire). The schema documents the contract so any UI
variant — or this test — can build representative payloads and confirm they
match the agreed shape.
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


def test_proposal_presented_event_validates(schema):
    event = {
        "event": "proposal_presented",
        "category": "python-web",
        "category_type": "framework",
        "proposed_pick": "fastapi",
        "alternatives": ["django", "flask"],
        "evidence": {
            "repo_count": 4,
            "most_recent": "2026-04-01T00:00:00+00:00",
            "confidence_qualifier": None,
        },
        "queue_position": {"index": 1, "total": 5},
    }
    jsonschema.validate(event, schema)


def test_user_response_accept_validates(schema):
    jsonschema.validate({"action": "accept"}, schema)


def test_user_response_skip_validates(schema):
    jsonschema.validate({"action": "skip"}, schema)


def test_user_response_defer_validates(schema):
    jsonschema.validate({"action": "defer"}, schema)


def test_user_response_change_requires_pick(schema):
    jsonschema.validate(
        {"action": "change", "chosen_pick": "litestar", "source": "free_form"},
        schema,
    )
    # Missing chosen_pick on change must fail validation.
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"action": "change"}, schema)


def test_decision_applied_event_validates(schema):
    event = {
        "event": "decision_applied",
        "category": "python-web",
        "action": "accept",
        "chosen_pick": "fastapi",
        "slot_yaml_written": "slots/python-web.yaml",
    }
    jsonschema.validate(event, schema)


def test_decision_applied_skip_allows_null_pick(schema):
    event = {
        "event": "decision_applied",
        "category": "python-web",
        "action": "skip",
        "chosen_pick": None,
        "slot_yaml_written": None,
    }
    jsonschema.validate(event, schema)


def test_deep_dive_offered_event_validates(schema):
    event = {
        "event": "deep_dive_offered",
        "category": "python-web",
        "pick": "fastapi",
        "default_response": "yes",
    }
    jsonschema.validate(event, schema)


def test_run_summary_event_validates(schema):
    event = {
        "event": "run_summary",
        "run_id": "abc-123",
        "accepted": 4,
        "changed": 1,
        "skipped": 0,
        "deferred": 2,
        "skipped_sources": [{"source_id": "org:secret-corp", "reason": "access denied"}],
        "deep_dive_failures": [{"category": "python-ai", "error": "deep-dive script timeout"}],
    }
    jsonschema.validate(event, schema)


def test_run_summary_event_minimum_shape_validates(schema):
    event = {
        "event": "run_summary",
        "run_id": "abc-123",
        "accepted": 0,
        "changed": 0,
        "skipped": 0,
        "deferred": 0,
        "skipped_sources": [],
    }
    jsonschema.validate(event, schema)
