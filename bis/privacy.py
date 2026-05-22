"""Trust-boundary scrubber.

This is the SOLE entry point for constructing the `SafePayload` type, which is
the only type permitted as input to LLM-bound functions in `bis.categories`.
FR-013 / SC-008 hinge on the rule: package names, manifest format NAMES,
frequencies, and recency timestamps are the only data crossing the boundary.

If you find yourself wanting to add a field to `SafePayload`, that is a privacy
decision — re-read FR-013 in specs/001-bootstrap-discovery/spec.md.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from bis.models import ProfileSnapshot, SafePayload, SafePayloadItem

# Bumped when scanner output shape changes; cache files with a different value
# are treated as miss (see bis.cache module docstring).
SCANNER_VERSION = "1"


def to_safe_payload(profile: ProfileSnapshot) -> SafePayload:
    """Aggregate the per-signal records in `profile` into a privacy-safe payload.

    Raises `TypeError` if anything other than a `ProfileSnapshot` is passed —
    this enforces the trust-boundary check at the call site.
    """

    if not isinstance(profile, ProfileSnapshot):
        raise TypeError(f"to_safe_payload requires ProfileSnapshot, got {type(profile).__name__}")

    # Aggregate by (package_name, manifest_format).
    counts: dict[tuple[str, str], int] = defaultdict(int)
    recencies: dict[tuple[str, str], datetime] = {}
    for sig in profile.signals:
        key = (sig.package_name, sig.manifest_format)
        counts[key] += 1
        prev = recencies.get(key)
        if prev is None or sig.observed_at > prev:
            recencies[key] = sig.observed_at

    items = [
        SafePayloadItem(
            package_name=name,
            manifest_format=fmt,
            repo_count=count,
            most_recent=recencies[(name, fmt)],
        )
        for (name, fmt), count in sorted(counts.items())
    ]
    return SafePayload(items=items)


__all__ = ["SCANNER_VERSION", "to_safe_payload"]
