"""Scale + Offset step: y = x * scale + offset"""

from typing import Any


def scale_offset_step(value: float, quality: str, params: dict[str, Any],
                       history: list[float]) -> tuple[float, str, list[str]]:
    """Apply linear transformation: y = x * scale + offset"""
    scale = float(params.get("scale", 1.0))
    offset = float(params.get("offset", 0.0))
    new_value = value * scale + offset
    warnings = []
    if scale != 1.0 or offset != 0.0:
        warnings.append(f"Applied scale={scale}, offset={offset}: {value} → {new_value}")
    return round(new_value, 6), quality, warnings
