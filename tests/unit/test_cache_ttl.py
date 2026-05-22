"""Unit tests for the per-repo cache TTL behavior (T019, FR-015, R-1)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bis.cache import get_cached_scan, put_cached_scan
from bis.models import CachedRepoScan, RepoRef
from bis.privacy import SCANNER_VERSION


def _repo() -> RepoRef:
    return RepoRef(
        owner="user",
        name="proj",
        last_pushed=datetime(2026, 5, 1, tzinfo=timezone.utc),
        is_private=False,
        is_org=False,
    )


def test_cache_miss_when_no_file(tmp_cache_root):
    assert get_cached_scan(_repo()) is None


def test_cache_round_trip_when_fresh(tmp_cache_root):
    scan = CachedRepoScan(
        repo=_repo(),
        scanned_at=datetime.now(timezone.utc),
        signals=[],
        scanner_version=SCANNER_VERSION,
    )
    put_cached_scan(scan)
    got = get_cached_scan(_repo())
    assert got is not None
    assert got.repo.slug == "user/proj"


def test_cache_expires_after_ttl(tmp_cache_root):
    stale = CachedRepoScan(
        repo=_repo(),
        scanned_at=datetime.now(timezone.utc) - timedelta(hours=25),
        signals=[],
        scanner_version=SCANNER_VERSION,
    )
    put_cached_scan(stale)
    assert get_cached_scan(_repo(), ttl=timedelta(hours=24)) is None


def test_cache_invalidates_on_scanner_version_mismatch(tmp_cache_root):
    scan = CachedRepoScan(
        repo=_repo(),
        scanned_at=datetime.now(timezone.utc),
        signals=[],
        scanner_version="999",  # mismatch
    )
    put_cached_scan(scan)
    assert get_cached_scan(_repo()) is None


def test_cache_layout_one_file_per_repo(tmp_cache_root):
    scan = CachedRepoScan(
        repo=_repo(),
        scanned_at=datetime.now(timezone.utc),
        signals=[],
        scanner_version=SCANNER_VERSION,
    )
    path = put_cached_scan(scan)
    assert path.name == "proj.yaml"
    assert path.parent.name == "user"
