"""Clamp step: clamp value to [min, max] range."""

from typing import Any


def clamp_step(value: float, quality: str, params: dict[str, Any],
                history: list[float]) -> tuple[float, str, list[str]]:
    """Clamp value to [min, max] range."""
    min_val = float(params.get("min", 0.0))
    max_val = float(params.get("max", 100.0))
    warnings = []
    clamped = max(min_val, min(max_val, value))
    if clamped != value:
        warnings.append(f"Clamped {value} to [{min_val}, {max_val}] → {clamped}")
    return clamped, quality, warnings
