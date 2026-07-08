"""Stale Check step: set quality STALE if timestamp older than max_age."""

from datetime import datetime, timezone
from typing import Any


def stale_check_step(value: float, quality: str, params: dict[str, Any],
                      history: list[float],
                      timestamp: datetime | None = None) -> tuple[float, str, list[str]]:
    """Set quality to STALE if timestamp older than max_age_seconds."""
    max_age = int(params.get("max_age_seconds", 60))
    warnings = []

    now = datetime.now(timezone.utc)
    ts = timestamp or now
    age = (now - ts).total_seconds()

    if age > max_age:
        new_quality = "STALE"
        warnings.append(f"Stale data: age={age:.0f}s > max_age={max_age}s — setting STALE")
        return value, new_quality, warnings

    return value, quality, warnings
