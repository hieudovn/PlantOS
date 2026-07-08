"""Processing step library — 7 MVP pure functions.

Each step is a pure function: (value, quality, params, history) -> (new_value, new_quality, warnings).
All steps return a (float, str, list[str]) tuple where:
  - float: the transformed value
  - str: the quality ("GOOD", "STALE", or "BAD")
  - list[str]: warning messages during processing
"""

from agent.processing.steps.scale_offset import scale_offset_step
from agent.processing.steps.linear_calibration import linear_calibration_step
from agent.processing.steps.clamp import clamp_step
from agent.processing.steps.moving_average import moving_average_step
from agent.processing.steps.quality_range import quality_range_step
from agent.processing.steps.stale_check import stale_check_step
from agent.processing.steps.baseline_subtract import baseline_subtract_step

STEP_REGISTRY: dict[str, callable] = {
    "scale_offset": scale_offset_step,
    "linear_calibration": linear_calibration_step,
    "clamp": clamp_step,
    "moving_average": moving_average_step,
    "quality_range": quality_range_step,
    "stale_check": stale_check_step,
    "baseline_subtract": baseline_subtract_step,
}
