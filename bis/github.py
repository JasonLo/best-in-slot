"""Subprocess wrappers around `gh` for the GitHub data we need.

Per constitution Principle V: every GitHub call goes through `gh api`. We never
read `GITHUB_TOKEN`, never use a Python SDK. Errors are degraded into
`SkippedSource` records rather than raised, so a partial run still completes.
"""

from __future__ import annotations

import base64
import json
import subprocess
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from bis.models import RepoRef, SkippedSource

GH_BIN = "gh"

# Subset of formats we care about — comes from scanner.KNOWN_FORMATS but kept
# decoupled to avoid an import cycle.
_DEFAULT_MANIFEST_FORMATS: set[str] = {
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "go.mod",
    "Cargo.toml",
    "Gemfile",
}


class GhUnavailable(RuntimeError):
    """Raised by `check_auth` when `gh` is missing or unauthenticated."""


def check_auth() -> None:
    """Raise `GhUnavailable` unless `gh auth status` exits 0."""

    try:
        result = subprocess.run(
            [GH_BIN, "auth", "status"], capture_output=True, text=True, timeout=10
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise GhUnavailable("gh CLI not available") from exc
    if result.returncode != 0:
        raise GhUnavailable(result.stderr.strip() or "gh auth status failed")


def _gh_api(endpoint: str) -> dict | list:
    """Call `gh api <endpoint>` and parse JSON. Raises `subprocess.CalledProcessError`
    on non-zero exit; callers should catch and translate to `SkippedSource`.
    """

    result = subprocess.run(
        [GH_BIN, "api", endpoint],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return json.loads(result.stdout)


def _gh_api_paged(endpoint: str, per_page: int = 100) -> Iterable[dict]:
    """Paginate `gh api` using `--paginate`. Yields individual items."""

    sep = "&" if "?" in endpoint else "?"
    paged = f"{endpoint}{sep}per_page={per_page}"
    result = subprocess.run(
        [GH_BIN, "api", paged, "--paginate"],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    # gh --paginate concatenates JSON arrays into one big JSON document.
    # The simplest safe parse: split by NDJSON or treat each line.
    text = result.stdout.strip()
    if not text:
        return []
    # gh --paginate returns one concatenated JSON array
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        # Fallback: one JSON array per line
        items: list[dict] = []
        for line in text.splitlines():
            chunk = json.loads(line)
            if isinstance(chunk, list):
                items.extend(chunk)
            else:
                items.append(chunk)
        return items


# --------------------------------------------------------------------------- listing


def _within_window(pushed_at: str, window: timedelta, now: datetime) -> bool:
    when = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    return (now - when) <= window


def list_user_repos(
    window: timedelta, now: datetime | None = None
) -> tuple[list[RepoRef], list[SkippedSource]]:
    """Return repos the authenticated user owns with activity in the trailing window."""

    now = now or datetime.now(UTC)
    skipped: list[SkippedSource] = []
    try:
        items = list(_gh_api_paged("/user/repos?affiliation=owner,collaborator&sort=pushed"))
    except subprocess.CalledProcessError as exc:
        skipped.append(SkippedSource(source_id="user:repos", reason=_stderr_reason(exc)))
        return [], skipped
    refs = _repos_from_items(items, window, now)
    return refs, skipped


def list_user_orgs() -> tuple[list[str], list[SkippedSource]]:
    skipped: list[SkippedSource] = []
    try:
        items = list(_gh_api_paged("/user/orgs"))
    except subprocess.CalledProcessError as exc:
        skipped.append(SkippedSource(source_id="user:orgs", reason=_stderr_reason(exc)))
        return [], skipped
    return [item["login"] for item in items if "login" in item], skipped


def list_org_repos(
    org: str, window: timedelta, now: datetime | None = None
) -> tuple[list[RepoRef], list[SkippedSource]]:
    now = now or datetime.now(UTC)
    skipped: list[SkippedSource] = []
    try:
        items = list(_gh_api_paged(f"/orgs/{org}/repos?type=all&sort=pushed"))
    except subprocess.CalledProcessError as exc:
        skipped.append(SkippedSource(source_id=f"org:{org}", reason=_stderr_reason(exc)))
        return [], skipped
    return _repos_from_items(items, window, now, is_org=True), skipped


def _repos_from_items(
    items: Iterable[dict], window: timedelta, now: datetime, *, is_org: bool | None = None
) -> list[RepoRef]:
    refs: list[RepoRef] = []
    for item in items:
        pushed = item.get("pushed_at") or item.get("updated_at")
        if not pushed:
            continue
        if not _within_window(pushed, window, now):
            continue
        owner_obj = item.get("owner", {}) or {}
        owner_login = owner_obj.get("login") or item.get("full_name", "/").split("/")[0]
        owner_type = owner_obj.get("type", "User")
        refs.append(
            RepoRef(
                owner=owner_login,
                name=item["name"],
                last_pushed=datetime.fromisoformat(pushed.replace("Z", "+00:00")),
                is_private=bool(item.get("private", False)),
                is_org=is_org if is_org is not None else owner_type == "Organization",
            )
        )
    return refs


# --------------------------------------------------------------------------- manifest fetch


def get_manifest_paths(
    repo: RepoRef, formats: set[str] | None = None
) -> tuple[list[str], list[SkippedSource]]:
    """Return manifest file paths in a repo whose basename matches a known format.

    Uses GitHub's `/repos/{owner}/{repo}/git/trees/HEAD?recursive=1` endpoint.
    """

    formats = formats or _DEFAULT_MANIFEST_FORMATS
    skipped: list[SkippedSource] = []
    try:
        tree = _gh_api(f"/repos/{repo.owner}/{repo.name}/git/trees/HEAD?recursive=1")
    except subprocess.CalledProcessError as exc:
        skipped.append(SkippedSource(source_id=f"repo:{repo.slug}", reason=_stderr_reason(exc)))
        return [], skipped
    if not isinstance(tree, dict):
        return [], skipped
    paths: list[str] = []
    for entry in tree.get("tree", []) or []:
        if entry.get("type") != "blob":
            continue
        path = entry.get("path", "")
        base = path.rsplit("/", 1)[-1]
        if base in formats or (base == "requirements.txt" or base.startswith("requirements-")):
            paths.append(path)
    return paths, skipped


def get_manifest_content(repo: RepoRef, path: str) -> str:
    """Fetch the raw content of a single manifest file via the contents endpoint."""

    payload = _gh_api(f"/repos/{repo.owner}/{repo.name}/contents/{path}")
    if not isinstance(payload, dict):
        raise ValueError(f"unexpected contents payload for {repo.slug}:{path}")
    content_b64 = payload.get("content", "")
    return base64.b64decode(content_b64).decode("utf-8", errors="replace")


# --------------------------------------------------------------------------- helpers


def _stderr_reason(exc: subprocess.CalledProcessError) -> str:
    return (exc.stderr or "").strip() or f"gh exited {exc.returncode}"


__all__ = [
    "GhUnavailable",
    "check_auth",
    "get_manifest_content",
    "get_manifest_paths",
    "list_org_repos",
    "list_user_orgs",
    "list_user_repos",
]
