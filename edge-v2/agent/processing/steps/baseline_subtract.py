"""Baseline Subtract step: y = x - baseline."""

from typing import Any


def baseline_subtract_step(value: float, quality: str, params: dict[str, Any],
                            history: list[float]) -> tuple[float, str, list[str]]:
    """Subtract baseline value: y = x - baseline."""
    baseline = float(params.get("baseline", 0.0))
    new_value = value - baseline
    warnings = []
    if baseline != 0.0:
        warnings.append(f"Subtracted baseline={baseline}: {value} → {new_value}")
    return round(new_value, 6), quality, warnings
