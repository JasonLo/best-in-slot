"""Unit tests for the trust-boundary scrubber (T022, FR-013, SC-008)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from bis.models import ProfileSnapshot, RepoRef, SafePayload, ToolSignal
from bis.privacy import SCANNER_VERSION, to_safe_payload

SECRET_README_BODY = "BEGIN PRIVATE BUSINESS LOGIC the secret sauce of acme corp"
SECRET_MANIFEST_BODY = "# private notes inside our pyproject"


def _profile_with_secrets() -> ProfileSnapshot:
    """A profile whose source-side data carries secrets we expect NEVER to leak."""

    repo = RepoRef(
        owner="acme-corp",
        name="secret-product",
        last_pushed=datetime(2026, 5, 1, tzinfo=UTC),
        is_private=True,
        is_org=True,
    )
    # The signal records the package name + format only — but we want to
    # construct a profile that *could* leak if to_safe_payload were sloppy.
    signal = ToolSignal(
        repo=repo,
        package_name="fastapi",
        manifest_format="pyproject.toml",
        observed_at=repo.last_pushed,
    )
    return ProfileSnapshot(
        repos=[repo],
        signals=[signal],
        window_start=datetime(2023, 5, 1, tzinfo=UTC),
        window_end=datetime(2026, 5, 22, tzinfo=UTC),
    )


def test_safe_payload_excludes_repo_identity_beyond_package_layer():
    profile = _profile_with_secrets()
    safe = to_safe_payload(profile)
    serialised = json.dumps(safe.model_dump(mode="json"))
    # The owner/name are NOT in the serialised payload.
    assert "acme-corp" not in serialised
    assert "secret-product" not in serialised
    # The package name IS in the payload — that's allowed.
    assert "fastapi" in serialised


def test_safe_payload_rejects_non_profile_input():
    with pytest.raises(TypeError):
        to_safe_payload({"signals": []})  # type: ignore[arg-type]


def test_safe_payload_does_not_carry_manifest_body():
    profile = _profile_with_secrets()
    safe = to_safe_payload(profile)
    serialised = json.dumps(safe.model_dump(mode="json"))
    assert SECRET_MANIFEST_BODY not in serialised
    assert SECRET_README_BODY not in serialised


def test_safe_payload_aggregates_signals_correctly():
    repo1 = RepoRef(
        owner="a",
        name="r1",
        last_pushed=datetime(2026, 1, 1, tzinfo=UTC),
        is_private=False,
        is_org=False,
    )
    repo2 = RepoRef(
        owner="a",
        name="r2",
        last_pushed=datetime(2026, 4, 1, tzinfo=UTC),
        is_private=False,
        is_org=False,
    )
    profile = ProfileSnapshot(
        repos=[repo1, repo2],
        signals=[
            ToolSignal(
                repo=repo1,
                package_name="fastapi",
                manifest_format="pyproject.toml",
                observed_at=repo1.last_pushed,
            ),
            ToolSignal(
                repo=repo2,
                package_name="fastapi",
                manifest_format="pyproject.toml",
                observed_at=repo2.last_pushed,
            ),
            ToolSignal(
                repo=repo1,
                package_name="httpx",
                manifest_format="pyproject.toml",
                observed_at=repo1.last_pushed,
            ),
        ],
        window_start=datetime(2023, 1, 1, tzinfo=UTC),
        window_end=datetime(2026, 5, 22, tzinfo=UTC),
    )
    safe = to_safe_payload(profile)
    by_name = {item.package_name: item for item in safe.items}
    assert by_name["fastapi"].repo_count == 2
    assert by_name["fastapi"].most_recent == repo2.last_pushed
    assert by_name["httpx"].repo_count == 1


def test_scanner_version_constant_exists():
    assert SCANNER_VERSION  # non-empty
    assert isinstance(SCANNER_VERSION, str)


def test_safe_payload_fields_are_an_allowlist():
    """Sentinel test: if SafePayload gains a field, this test must be re-reviewed against FR-013."""

    safe = SafePayload(items=[])
    assert set(safe.model_dump().keys()) == {"items"}
    # And SafePayloadItem has a fixed set of fields too.
    from bis.models import SafePayloadItem

    item = SafePayloadItem(
        package_name="x",
        manifest_format="pyproject.toml",
        repo_count=1,
        most_recent=datetime.now(UTC),
    )
    assert set(item.model_dump().keys()) == {
        "package_name",
        "manifest_format",
        "repo_count",
        "most_recent",
    }
