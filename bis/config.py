"""Project settings loaded from `settings.yaml` with sane defaults.

The bootstrap pipeline reads a single `Settings` instance via `load_settings()`.
Missing file or missing fields → defaults; explicit values override.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class Settings(BaseModel):
    """Project-wide settings; serialised to/from `settings.yaml`."""

    model_config = ConfigDict(extra="forbid")

    mining_window_years: int = Field(default=3, ge=1, le=10)
    cache_ttl_hours: int = Field(default=24, ge=1)
    cache_root: Path = Field(default=Path(".bis/cache/repos"))
    slots_root: Path = Field(default=Path("slots"))

    @property
    def mining_window(self) -> timedelta:
        return timedelta(days=365 * self.mining_window_years)

    @property
    def cache_ttl(self) -> timedelta:
        return timedelta(hours=self.cache_ttl_hours)


def load_settings(path: Path | str = "settings.yaml") -> Settings:
    """Load `Settings` from a YAML file. Missing file → defaults."""

    p = Path(path)
    if not p.exists():
        return Settings()
    raw = yaml.safe_load(p.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{p}: expected a YAML mapping at the top level")
    return Settings(**raw)


__all__ = ["Settings", "load_settings"]
