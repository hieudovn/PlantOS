"""Moving Average (SMA) step: simple moving average with window size."""

from typing import Any


def moving_average_step(value: float, quality: str, params: dict[str, Any],
                         history: list[float]) -> tuple[float, str, list[str]]:
    """Simple moving average with configurable window size."""
    window = int(params.get("window_size", 5))
    warnings = []

    # Use history + current value for the average
    samples = (history + [value])[-window:]
    avg = sum(samples) / len(samples)

    if len(samples) < window:
        warnings.append(f"Moving average: only {len(samples)}/{window} samples available")
    else:
        warnings.append(f"Moving average (window={window}): {value} → {avg}")

    return round(avg, 6), quality, warnings
