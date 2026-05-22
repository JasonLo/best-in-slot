"""YAML CRUD for slot state and bootstrap-run state.

`slots/{category}.yaml`  → one `SlotState` per file
`slots/.bootstrap.yaml`  → one `BootstrapRunState` (overwritten per run)

Per constitution Principle II, this module is the sole authority for slot
state persistence. Append-only history is enforced here: `append_history`
adds an entry; there is no `edit_history` or `delete_history` API.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from bis.models import BootstrapRunState, HistoryEntry, SlotState

_BOOTSTRAP_FILE = ".bootstrap.yaml"


def slots_root() -> Path:
    override = os.environ.get("BIS_SLOTS_ROOT")
    if override:
        return Path(override)
    return Path("slots")


def _slot_path(category: str) -> Path:
    return slots_root() / f"{category}.yaml"


def _bootstrap_path() -> Path:
    return slots_root() / _BOOTSTRAP_FILE


# --------------------------------------------------------------------------- slot state


def read_slot_state(category: str) -> SlotState | None:
    path = _slot_path(category)
    if not path.exists():
        return None
    raw = yaml.safe_load(path.read_text()) or {}
    return SlotState.model_validate(raw)


def write_slot_state(state: SlotState) -> Path:
    path = _slot_path(state.category)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".yaml.tmp")
    tmp.write_text(yaml.safe_dump(state.model_dump(mode="json"), sort_keys=False))
    tmp.replace(path)
    return path


def append_history(category: str, entry: HistoryEntry) -> Path:
    state = read_slot_state(category)
    if state is None:
        raise ValueError(f"no slot state for category={category!r}; cannot append history")
    state = state.model_copy(update={"history": [*state.history, entry]})
    return write_slot_state(state)


def list_existing_slot_categories() -> list[str]:
    """Return the categories that already have a slot YAML on disk.

    Excludes the `.bootstrap.yaml` sidecar.
    """

    root = slots_root()
    if not root.exists():
        return []
    return sorted(
        p.stem
        for p in root.glob("*.yaml")
        if p.name != _BOOTSTRAP_FILE and not p.name.startswith(".")
    )


# --------------------------------------------------------------------------- bootstrap run state


def read_bootstrap_run_state() -> BootstrapRunState | None:
    path = _bootstrap_path()
    if not path.exists():
        return None
    raw = yaml.safe_load(path.read_text()) or {}
    return BootstrapRunState.model_validate(raw)


def write_bootstrap_run_state(state: BootstrapRunState) -> Path:
    path = _bootstrap_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".yaml.tmp")
    tmp.write_text(yaml.safe_dump(state.model_dump(mode="json"), sort_keys=False))
    tmp.replace(path)
    return path


__all__ = [
    "append_history",
    "list_existing_slot_categories",
    "read_bootstrap_run_state",
    "read_slot_state",
    "slots_root",
    "write_bootstrap_run_state",
    "write_slot_state",
]
