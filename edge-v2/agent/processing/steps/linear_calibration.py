"""Linear Calibration step: y = a * x + b"""

from typing import Any


def linear_calibration_step(value: float, quality: str, params: dict[str, Any],
                             history: list[float]) -> tuple[float, str, list[str]]:
    """Apply calibration curve: y = a * x + b"""
    a = float(params.get("a", 1.0))
    b = float(params.get("b", 0.0))
    new_value = a * value + b
    warnings = []
    if a != 1.0 or b != 0.0:
        warnings.append(f"Applied calibration a={a}, b={b}: {value} → {new_value}")
    return round(new_value, 6), quality, warnings
