"""Unit tests for manifest parsers (T023)."""

from __future__ import annotations

import pytest

from bis.scanner import KNOWN_FORMATS, scan_manifest

PYPROJECT = """
[project]
name = "demo"
dependencies = ["FastAPI>=0.115", "httpx[http2]>=0.27", "pydantic"]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff"]
"""

REQUIREMENTS = """\
# top-level deps
fastapi==0.115.0  ; python_version >= "3.11"
HTTPX>=0.27.0
ruff

-r dev-requirements.txt
"""

PACKAGE_JSON = """
{
  "name": "demo",
  "dependencies": {
    "react": "^19.0.0",
    "@scope/lib": "^1.0.0"
  },
  "devDependencies": {
    "vite": "^5.0.0"
  }
}
"""

GO_MOD = """\
module example.com/demo

go 1.22

require (
    github.com/gin-gonic/gin v1.10.0
    golang.org/x/sync v0.7.0
)
"""

CARGO_TOML = """
[package]
name = "demo"

[dependencies]
serde = "1.0"
tokio = { version = "1", features = ["full"] }

[dev-dependencies]
mockito = "1"
"""

GEMFILE = """\
source 'https://rubygems.org'

gem 'rails', '~> 7.1'
gem 'puma'
# gem 'commented-out'
"""


@pytest.mark.parametrize(
    "filename,content,expected_subset",
    [
        ("pyproject.toml", PYPROJECT, {"fastapi", "httpx", "pydantic", "pytest", "ruff"}),
        ("requirements.txt", REQUIREMENTS, {"fastapi", "httpx", "ruff"}),
        ("package.json", PACKAGE_JSON, {"react", "@scope/lib", "vite"}),
        ("go.mod", GO_MOD, {"github.com/gin-gonic/gin", "golang.org/x/sync"}),
        ("Cargo.toml", CARGO_TOML, {"serde", "tokio", "mockito"}),
        ("Gemfile", GEMFILE, {"rails", "puma"}),
    ],
)
def test_parsers_extract_expected_names(filename, content, expected_subset):
    result = set(scan_manifest(filename, content))
    assert expected_subset.issubset(result), f"missing: {expected_subset - result}"


def test_python_normalisation_lowercase_dashed():
    result = scan_manifest("pyproject.toml", '[project]\ndependencies = ["My_Package>=1.0"]\n')
    assert result == ["my-package"]


def test_unknown_format_raises():
    with pytest.raises(ValueError):
        scan_manifest("Makefile", "")


def test_known_formats_set_matches_parsers():
    expected = {
        "pyproject.toml",
        "requirements.txt",
        "package.json",
        "go.mod",
        "Cargo.toml",
        "Gemfile",
    }
    assert expected == KNOWN_FORMATS
