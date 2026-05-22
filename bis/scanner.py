"""Manifest parsers for the mining phase.

Each parser takes the raw text of a single manifest file and returns a list of
normalised package names. Normalisation rules (per constitution):
- Lowercase
- Dashes-not-underscores for Python packages
- Scoped names preserved for npm (e.g. `@scope/pkg`)
"""

from __future__ import annotations

import json
import re
import tomllib
from collections.abc import Iterable
from pathlib import Path

KNOWN_FORMATS: set[str] = {
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "go.mod",
    "Cargo.toml",
    "Gemfile",
}


# --------------------------------------------------------------------------- normalisation


_PY_NORMALISE = re.compile(r"[_\.]+")


def _normalise_python(name: str) -> str:
    return _PY_NORMALISE.sub("-", name.strip().lower())


def _normalise_npm(name: str) -> str:
    return name.strip().lower()


def _normalise_go(name: str) -> str:
    # Go modules keep their import path (lowercased).
    return name.strip().lower()


def _normalise_passthrough(name: str) -> str:
    return name.strip().lower()


# --------------------------------------------------------------------------- per-format parsers


def _parse_pyproject(content: str) -> list[str]:
    data = tomllib.loads(content)
    found: list[str] = []
    project = data.get("project", {})
    found.extend(_dep_spec_to_names(project.get("dependencies", []) or []))
    for group_deps in (project.get("optional-dependencies", {}) or {}).values():
        found.extend(_dep_spec_to_names(group_deps))

    tool = data.get("tool", {})
    poetry_deps = (tool.get("poetry", {}) or {}).get("dependencies", {}) or {}
    found.extend(name for name in poetry_deps if name != "python")
    pixi_deps = (tool.get("pixi", {}) or {}).get("dependencies", {}) or {}
    found.extend(name for name in pixi_deps if name != "python")

    return _dedupe([_normalise_python(n) for n in found if n])


def _dep_spec_to_names(specs: Iterable[str]) -> list[str]:
    """Extract package names from PEP 508 dependency strings.

    Strips extras, version specifiers, environment markers, and URLs.
    """
    names: list[str] = []
    for spec in specs:
        # Take everything before the first occurrence of any specifier char.
        m = re.match(r"\s*([A-Za-z0-9_.\-]+)", spec)
        if m:
            names.append(m.group(1))
    return names


def _parse_requirements(content: str) -> list[str]:
    names: list[str] = []
    for raw in content.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        m = re.match(r"([A-Za-z0-9_.\-]+)", line)
        if m:
            names.append(_normalise_python(m.group(1)))
    return _dedupe(names)


def _parse_package_json(content: str) -> list[str]:
    data = json.loads(content)
    found: list[str] = []
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        deps = data.get(key) or {}
        found.extend(deps.keys())
    return _dedupe([_normalise_npm(n) for n in found if n])


_GO_REQUIRE_LINE = re.compile(r"^\s*([\w./\-]+)\s+v[\w.\-+]+")


def _parse_go_mod(content: str) -> list[str]:
    """Extract `require` block entries from a go.mod file."""

    names: list[str] = []
    in_block = False
    for raw in content.splitlines():
        line = raw.strip()
        if line.startswith("require ("):
            in_block = True
            continue
        if in_block:
            if line.startswith(")"):
                in_block = False
                continue
            m = _GO_REQUIRE_LINE.match(line)
            if m:
                names.append(_normalise_go(m.group(1)))
            continue
        if line.startswith("require "):
            tail = line[len("require ") :].strip()
            m = _GO_REQUIRE_LINE.match(tail)
            if m:
                names.append(_normalise_go(m.group(1)))
    return _dedupe(names)


def _parse_cargo_toml(content: str) -> list[str]:
    data = tomllib.loads(content)
    found: list[str] = []
    for key in ("dependencies", "dev-dependencies", "build-dependencies"):
        deps = data.get(key, {}) or {}
        found.extend(deps.keys())
    return _dedupe([_normalise_passthrough(n) for n in found if n])


_GEMFILE_LINE = re.compile(r"""^\s*gem\s+['"]([^'"]+)['"]""")


def _parse_gemfile(content: str) -> list[str]:
    names: list[str] = []
    for raw in content.splitlines():
        m = _GEMFILE_LINE.match(raw)
        if m:
            names.append(_normalise_passthrough(m.group(1)))
    return _dedupe(names)


# --------------------------------------------------------------------------- public API


_PARSERS = {
    "pyproject.toml": _parse_pyproject,
    "package.json": _parse_package_json,
    "go.mod": _parse_go_mod,
    "Cargo.toml": _parse_cargo_toml,
    "Gemfile": _parse_gemfile,
}


def scan_manifest(path: Path | str, content: str) -> list[str]:
    """Dispatch on the filename and return normalised package names."""

    name = Path(path).name
    parser = _PARSERS.get(name)
    if parser is not None:
        return parser(content)
    if name == "requirements.txt" or name.startswith("requirements-"):
        return _parse_requirements(content)
    raise ValueError(f"unsupported manifest format: {name}")


def _dedupe(seq: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in seq:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


__all__ = ["KNOWN_FORMATS", "scan_manifest"]
