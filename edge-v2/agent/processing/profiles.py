"""ProcessingProfile and ProcessedReading data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ProcessingStep:
    """A single step in a processing pipeline."""
    type: str  # One of 7 MVP types
    params: dict[str, Any] = field(default_factory=dict)
    order: int = 0
    enabled: bool = True


@dataclass
class ProcessingProfile:
    """A named processing profile containing an ordered list of steps."""
    profile_id: str
    name: str
    description: str = ""
    steps: list[ProcessingStep] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def add_step(self, step_type: str, params: dict | None = None, order: int | None = None) -> ProcessingStep:
        order = order or len(self.steps)
        step = ProcessingStep(type=step_type, params=params or {}, order=order)
        self.steps.append(step)
        self.steps.sort(key=lambda s: s.order)
        return step

    def remove_step(self, order: int) -> bool:
        self.steps = [s for s in self.steps if s.order != order]
        return True


@dataclass
class ProcessedReading:
    """Output from processing pipeline — stored in processed_measurements table."""
    signal_id: str
    value: float
    quality: str  # GOOD / STALE / BAD
    timestamp: datetime
    profile_id: str | None = None


# ---- 7 MVP step types metadata --------------------------------------------

MVP_STEP_TYPES: dict[str, dict[str, Any]] = {
    "scale_offset": {
        "name": "Scale + Offset",
        "description": "Apply linear transformation: y = x * scale + offset",
        "params": {
            "scale": {"type": "float", "default": 1.0, "description": "Multiplier"},
            "offset": {"type": "float", "default": 0.0, "description": "Additive offset"},
        },
    },
    "linear_calibration": {
        "name": "Linear Calibration",
        "description": "Apply calibration curve: y = a * x + b",
        "params": {
            "a": {"type": "float", "default": 1.0, "description": "Slope"},
            "b": {"type": "float", "default": 0.0, "description": "Intercept"},
        },
    },
    "clamp": {
        "name": "Clamp",
        "description": "Clamp value to [min, max] range",
        "params": {
            "min": {"type": "float", "default": 0.0, "description": "Minimum allowed value"},
            "max": {"type": "float", "default": 100.0, "description": "Maximum allowed value"},
        },
    },
    "moving_average": {
        "name": "Moving Average (SMA)",
        "description": "Simple moving average with configurable window size",
        "params": {
            "window_size": {"type": "int", "default": 5, "description": "Number of samples to average"},
        },
    },
    "quality_range": {
        "name": "Quality Range Check",
        "description": "Set quality to BAD if value outside [min, max]",
        "params": {
            "min": {"type": "float", "default": 0.0, "description": "Minimum acceptable value"},
            "max": {"type": "float", "default": 100.0, "description": "Maximum acceptable value"},
        },
    },
    "stale_check": {
        "name": "Stale Check",
        "description": "Set quality to STALE if no update within max_age",
        "params": {
            "max_age_seconds": {"type": "int", "default": 60, "description": "Max age before STALE"},
        },
    },
    "baseline_subtract": {
        "name": "Baseline Subtract",
        "description": "Subtract baseline value: y = x - baseline",
        "params": {
            "baseline": {"type": "float", "default": 0.0, "description": "Baseline value to subtract"},
        },
    },
}

# Steps that will be added post-MVP (shown as "Coming Soon" in UI)
COMING_SOON_STEPS: list[str] = [
    "median_filter", "low_pass", "delta", "rate_of_change",
    "boolean_map", "enum_map", "unit_conversion", "deadband",
]
