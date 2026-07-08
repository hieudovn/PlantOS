"""Allowed values for asset classification fields."""

ASSET_TYPES = [
    "pump", "filter", "tank", "motor", "sensor_array",
    "valve", "meter", "compressor_train", "compressor", "heat_exchanger",
    "centrifuge", "fan", "agitator", "mixer", "reactor",
    "blower", "boiler", "chiller", "cooling_tower", "generator",
    "transformer", "switchgear", "panel", "conveyor",
    "custom_equipment",
]

ASSET_ROLES = [
    "equipment", "functional_location", "subsystem", "component", "logical_group",
]

LIFECYCLE_STATUSES = ["active", "inactive", "maintenance", "retired", "deleted"]

CRITICALITY_LEVELS = ["low", "medium", "high", "critical"]
