"""Quality Range Check step: set quality BAD if value outside [min, max]."""

from typing import Any


def quality_range_step(value: float, quality: str, params: dict[str, Any],
                        history: list[float]) -> tuple[float, str, list[str]]:
    """Set quality to BAD if value outside [min, max]."""
    min_val = float(params.get("min", 0.0))
    max_val = float(params.get("max", 100.0))
    warnings = []

    if value < min_val or value > max_val:
        new_quality = "BAD"
        warnings.append(f"Quality range violation: {value} outside [{min_val}, {max_val}] — setting BAD")
        return value, new_quality, warnings

    return value, quality, warnings
