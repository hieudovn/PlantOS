"""Contract validator — structural + cross-reference validation.

Implements 18 validation rules from the Integration Contract specification.
Does NOT access database — purely stateless validation.
"""

import re
from typing import Any

VALID_ASSET_TYPES = {
    "compressor_train", "compressor", "pump", "motor", "turbine", "fan", "gearbox",
    "tank", "vessel", "heat_exchanger", "cooling_tower", "boiler", "furnace",
    "reactor", "column", "bearing_assembly", "seal_system", "lubrication_system",
    "cooling_system", "transformer", "switchgear", "breaker", "feeder",
    "motor_control_center", "vfd", "valve", "control_valve", "safety_valve",
    "pipeline", "filter", "strainer", "sensor_array", "analyzer", "flow_meter",
    "transmitter", "production_line", "work_cell", "conveyor", "robot", "cnc_machine",
}

VALID_UNITS = {
    "kPa", "MPa", "bar", "psi", "Pa", "mbar",
    "degC", "degF", "K",
    "m3/h", "Nm3/h", "L/min", "kg/h", "t/h", "m3/s",
    "RPM", "Hz", "m/s", "rad/s",
    "A", "V", "kW", "kVA", "kWh", "PF", "ohm",
    "mm/s", "um", "mil", "g",
    "m", "mm", "cm", "%",
    "kg", "t", "g",
    "N", "kN", "Nm", "kNm",
    "kJ", "MJ", "kWh", "MWh", "W", "MW",
    "kg/m3", "g/cm3", "cSt", "cP",
}

VALID_CRITICALITY = {"critical", "high", "medium", "low"}
VALID_STATUS = {"active", "inactive", "deprecated"}
VALID_SIGNAL_TYPES = {"measurement", "status", "setpoint", "command"}
VALID_DATA_TYPES = {"float", "bool", "int", "string"}
OPCUA_NODE_PATTERN = re.compile(r"^ns=\d+;s=[A-Z][A-Z0-9_]*$")


class ValidationResult:
    def __init__(self):
        self.errors: list[dict] = []
        self.warnings: list[dict] = []

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0

    def error(self, path: str, message: str):
        self.errors.append({"path": path, "message": message})

    def warning(self, path: str, message: str):
        self.warnings.append({"path": path, "message": message})


def validate_contract(contract: dict) -> ValidationResult:
    """Validate a contract dict against all rules. Does NOT access database."""
    result = ValidationResult()

    plant = contract.get("plant", {})
    areas = contract.get("areas", [])
    assets = contract.get("assets", [])
    signals = contract.get("signals", [])
    bindings = contract.get("bindings", {})
    source = contract.get("source", {})

    # Build lookup sets
    area_ids = {a["area_id"] for a in areas}
    asset_ids = {a["asset_id"] for a in assets}
    signal_ids = {s["signal_id"] for s in signals}

    # V1: contract version valid semver
    version = contract.get("contract", {}).get("version", "")
    if not re.match(r"^\d+\.\d+(\.\d+)?$", version):
        result.error("contract.version", f"Invalid semver: '{version}'")

    # V2: plant_id present, valid format
    plant_id = plant.get("plant_id", "")
    if not re.match(r"^[A-Z][A-Z0-9-]*$", plant_id):
        result.error("plant.plant_id", f"Invalid format: '{plant_id}'")

    # V3: area.plant_id matches plant.plant_id
    for i, area in enumerate(areas):
        if area.get("plant_id") != plant_id:
            result.error(f"areas[{i}].plant_id",
                         f"Area plant_id '{area.get('plant_id')}' != plant.plant_id '{plant_id}'")

    # V4: asset.area_id exists
    for i, asset in enumerate(assets):
        aid = asset.get("area_id", "")
        if aid not in area_ids:
            result.error(f"assets[{i}].area_id", f"Area '{aid}' not found")

    # V5: asset.parent_asset_id exists or null
    for i, asset in enumerate(assets):
        pid = asset.get("parent_asset_id")
        if pid is not None and pid not in asset_ids:
            result.error(f"assets[{i}].parent_asset_id", f"Parent asset '{pid}' not found")

    # V6: signal.asset_id exists
    for i, sig in enumerate(signals):
        aid = sig.get("asset_id", "")
        if aid not in asset_ids:
            result.error(f"signals[{i}].asset_id", f"Asset '{aid}' not found")

    # V7-V9: uniqueness
    _check_duplicates(result, areas, "area_id", "areas")
    _check_duplicates(result, assets, "asset_id", "assets")
    _check_duplicates(result, signals, "signal_id", "signals")

    # V10: signal_id format {ASSET_ID}.{signal_name}
    for i, sig in enumerate(signals):
        sid = sig.get("signal_id", "")
        aid = sig.get("asset_id", "")
        sname = sig.get("signal_name", "")
        expected = f"{aid}.{sname}"
        if sid != expected:
            result.error(f"signals[{i}].signal_id",
                         f"Expected '{expected}', got '{sid}'")

    # V11: opcua_node_id format
    opcua = (bindings or {}).get("opcua", [])
    for i, b in enumerate(opcua):
        nid = b.get("node_id", "")
        if not OPCUA_NODE_PATTERN.match(nid):
            result.error(f"bindings.opcua[{i}].node_id", f"Invalid OPC UA NodeId: '{nid}'")

    # V12: engineering_unit recognized
    for i, sig in enumerate(signals):
        unit = sig.get("engineering_unit", "")
        if unit and unit not in VALID_UNITS:
            result.warning(f"signals[{i}].engineering_unit", f"Unrecognized unit: '{unit}'")

    # V13: asset_type recognized
    for i, asset in enumerate(assets):
        atype = asset.get("asset_type", "")
        if atype and atype not in VALID_ASSET_TYPES:
            result.warning(f"assets[{i}].asset_type", f"Unrecognized type: '{atype}'")

    # V14: status valid (default 'active' per Pydantic schema)
    for i, asset in enumerate(assets):
        status = asset.get("status", "active")
        if status not in VALID_STATUS:
            result.error(f"assets[{i}].status", f"Invalid status: '{status}'")
    for i, sig in enumerate(signals):
        status = sig.get("status", "active")
        if status not in VALID_STATUS:
            result.error(f"signals[{i}].status", f"Invalid status: '{status}'")

    # V15: criticality valid (default 'medium' per Pydantic schema)
    for i, asset in enumerate(assets):
        criticality = asset.get("criticality", "medium")
        if criticality not in VALID_CRITICALITY:
            result.error(f"assets[{i}].criticality", f"Invalid criticality: '{criticality}'")

    # V16: opcua binding signal_id references existing signal
    for i, b in enumerate(opcua):
        sid = b.get("signal_id", "")
        if sid not in signal_ids:
            result.error(f"bindings.opcua[{i}].signal_id", f"Signal '{sid}' not found")

    # V17: no duplicate opcua node_ids
    node_ids = [b.get("node_id") for b in opcua]
    seen = set()
    for i, nid in enumerate(node_ids):
        if nid and nid in seen:
            result.error(f"bindings.opcua[{i}].node_id", f"Duplicate OPC UA NodeId: '{nid}'")
        seen.add(nid)

    # V18: warning if signal has no opcua binding (when system_type expects it)
    src_type = source.get("system_type", "")
    if src_type in ("virtual_factory", "opcua"):
        bound_signals = {b.get("signal_id") for b in opcua}
        for sig_id in signal_ids:
            if sig_id not in bound_signals:
                result.warning(f"signals[{sig_id}]", f"Signal has no OPC UA binding (system_type={src_type})")

    return result


def _check_duplicates(result: ValidationResult, items: list, key: str, category: str):
    seen = {}
    for i, item in enumerate(items):
        val = item.get(key, "")
        if val and val in seen:
            result.error(f"{category}[{i}].{key}", f"Duplicate {key}: '{val}' (first at index {seen[val]})")
        seen[val] = i


def generate_uns_path(signal: dict, area: dict, asset: dict, plant: dict, uns_policy: dict) -> str:
    """Generate UNS path from contract entities."""
    template = uns_policy.get("path_template",
                               "{namespace_root}/{plant_id}/{area_id}/{asset_id}/{signal_name}")
    separator = uns_policy.get("separator", "/")

    path = template.format(
        namespace_root=uns_policy.get("namespace_root", ""),
        plant_id=plant.get("plant_id", ""),
        area_id=area.get("area_id", ""),
        asset_id=asset.get("asset_id", ""),
        signal_name=signal.get("signal_name", ""),
    )

    if uns_policy.get("normalize_case") == "lower":
        path = path.lower()

    return path.replace("/", separator)
