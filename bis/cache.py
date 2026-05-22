"""Per-repo mining cache with ~24h TTL (FR-015 / R-1).

Layout: one YAML file per repo at `<cache_root>/<owner>/<repo>.yaml`. The cache
root defaults to `.bis/cache/repos/` but can be overridden via the
`BIS_CACHE_ROOT` env var (used by tests via the `tmp_cache_root` fixture).

A cache entry is considered fresh when both:
  * `now - scanned_at < TTL`, AND
  * `scanned_at.scanner_version == SCANNER_VERSION`.

When the scanner's output shape changes, bump `SCANNER_VERSION` in
`bis.privacy`; existing cache files become misses and are refreshed on next
read. This is intentional — no migration ceremony, no in-place rewrite.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from bis.models import CachedRepoScan, RepoRef
from bis.privacy import SCANNER_VERSION


def cache_root() -> Path:
    override = os.environ.get("BIS_CACHE_ROOT")
    if override:
        return Path(override)
    return Path(".bis/cache/repos")


def _cache_path(repo: RepoRef) -> Path:
    return cache_root() / repo.owner / f"{repo.name}.yaml"


def get_cached_scan(repo: RepoRef, ttl: timedelta = timedelta(hours=24)) -> CachedRepoScan | None:
    """Return a cached scan if fresh; otherwise None."""

    path = _cache_path(repo)
    if not path.exists():
        return None
    try:
        raw = yaml.safe_load(path.read_text()) or {}
        cached = CachedRepoScan.model_validate(raw)
    except (yaml.YAMLError, ValueError):
        return None
    if cached.scanner_version != SCANNER_VERSION:
        return None
    if datetime.now(timezone.utc) - cached.scanned_at >= ttl:
        return None
    return cached


def put_cached_scan(scan: CachedRepoScan) -> Path:
    """Persist a scan record. Returns the path written."""

    path = _cache_path(scan.repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write: temp file then rename.
    tmp = path.with_suffix(".yaml.tmp")
    tmp.write_text(yaml.safe_dump(scan.model_dump(mode="json"), sort_keys=False))
    tmp.replace(path)
    return path


__all__ = ["cache_root", "get_cached_scan", "put_cached_scan"]
