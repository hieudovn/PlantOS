"""Process View Config — FastAPI router."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


# ---- Hardcoded WTP-DEMO-01 config (migrated from frontend config/plants/wtp-demo-01.ts) ----

WTP_WORKFLOW = [
    {"id": "intake", "label": "Intake", "area_id": "INTAKE-AREA", "kpi_signal_id": "RWP-101.flow_rate", "kpi_unit": "m3/h", "kpi_type": "signal"},
    {"id": "dosing", "label": "Dosing", "area_id": "CHEMICAL-DOSING-AREA", "kpi_signal_id": "CHEMICAL-CONSUMPTION-STATION-101.coagulant_dose_rate", "kpi_unit": "mg/L", "kpi_type": "signal"},
    {"id": "clarifier", "label": "Clarifier", "area_id": "CLARIFICATION-AREA", "kpi_signal_id": "CLARIFIER-101.settled_turbidity", "kpi_unit": "NTU", "kpi_type": "signal"},
    {"id": "filters", "label": "Filters", "area_id": "FILTRATION-AREA", "kpi_signal_id": "FILTER-QUALITY-STATION-101.filtered_turbidity", "kpi_unit": "NTU", "kpi_type": "signal"},
    {"id": "disinfection", "label": "Disinfection", "area_id": "DISINFECTION-CLEARWATER-AREA", "kpi_signal_id": "DISINFECTION-QUALITY-STATION-101.free_chlorine", "kpi_unit": "mg/L", "kpi_type": "signal"},
    {"id": "storage", "label": "Storage", "area_id": "DISINFECTION-CLEARWATER-AREA", "kpi_signal_id": "CLEAR-WATER-TANK-101.level", "kpi_unit": "%", "kpi_type": "signal"},
    {"id": "distribution", "label": "Distribution", "area_id": "DISTRIBUTION-AREA", "kpi_signal_id": "HSP-101.flow_rate", "kpi_unit": "m3/h", "kpi_type": "signal"},
]

WTP_AREAS = [
    {"area_id": "INTAKE-AREA", "name": "Intake Area", "asset_count": 1},
    {"area_id": "CHEMICAL-DOSING-AREA", "name": "Chemical Dosing Area", "asset_count": 1},
    {"area_id": "CLARIFICATION-AREA", "name": "Clarification Area", "asset_count": 1},
    {"area_id": "FILTRATION-AREA", "name": "Filtration Area", "asset_count": 4},
    {"area_id": "DISINFECTION-CLEARWATER-AREA", "name": "Disinfection & Clearwater", "asset_count": 3},
    {"area_id": "DISTRIBUTION-AREA", "name": "Distribution Area", "asset_count": 1},
]

WTP_CONDITION_CONFIGS = {
    "FILTER-101": {
        "signals": [
            {"signal_id": "FILTER-101.filter_dp", "label": "DP", "unit": "kPa"},
            {"signal_id": "FILTER-101.effluent_flow", "label": "Effluent", "unit": "m3/h"},
        ],
        "thresholds": {
            "FILTER-101.filter_dp": {"warn": 60, "crit": 80, "direction": "high"},
        },
        "kpi_ids": [],
    },
    "FILTER-102": {
        "signals": [
            {"signal_id": "FILTER-102.filter_dp", "label": "DP", "unit": "kPa"},
            {"signal_id": "FILTER-102.effluent_flow", "label": "Effluent", "unit": "m3/h"},
        ],
        "thresholds": {
            "FILTER-102.filter_dp": {"warn": 60, "crit": 80, "direction": "high"},
        },
        "kpi_ids": [],
    },
    "BACKWASH-PUMP-101": {
        "signals": [
            {"signal_id": "BACKWASH-PUMP-101.running_status", "label": "Status", "unit": ""},
        ],
        "thresholds": {},
        "kpi_ids": [],
    },
    "FILTER-QUALITY-STATION-101": {
        "signals": [
            {"signal_id": "FILTER-QUALITY-STATION-101.filtered_turbidity", "label": "Turbidity", "unit": "NTU"},
            {"signal_id": "FILTER-QUALITY-STATION-101.filter_run_quality_index", "label": "Quality", "unit": ""},
        ],
        "thresholds": {},
        "kpi_ids": [],
    },
}

WTP_THRESHOLDS = {
    "RWP-101.flow_rate": {"warn": 400, "crit": 200, "direction": "low"},
    "CHEMICAL-CONSUMPTION-STATION-101.coagulant_dose_rate": {"warn": 50, "crit": 80, "direction": "high"},
    "CLARIFIER-101.settled_turbidity": {"warn": 5, "crit": 10, "direction": "high"},
    "FILTER-QUALITY-STATION-101.filtered_turbidity": {"warn": 0.5, "crit": 1, "direction": "high"},
    "DISINFECTION-QUALITY-STATION-101.free_chlorine": {"warn": 0.8, "crit": 0.5, "direction": "low"},
    "CLEAR-WATER-TANK-101.level": {"warn": 30, "crit": 15, "direction": "low"},
    "HSP-101.flow_rate": {"warn": 300, "crit": 150, "direction": "low"},
}


# ---- Endpoints ----

@router.get("/plants/{plant_id}/process-view")
def get_process_view(plant_id: str):
    """Return the full process view configuration for a plant."""
    if plant_id == "WTP-DEMO-01":
        return {
            "plant_id": plant_id,
            "workflow": WTP_WORKFLOW,
            "areas": WTP_AREAS,
            "thresholds": WTP_THRESHOLDS,
            "source": "backend",
        }
    # For other plants, return empty config
    return {"plant_id": plant_id, "workflow": [], "areas": [], "thresholds": {}, "source": "backend"}


@router.get("/assets/{asset_id}/condition-config")
def get_condition_config(asset_id: str):
    """Return condition view config for an asset."""
    # Try to read from bindings first (future)
    # Fallback to hardcoded WTP config
    config = WTP_CONDITION_CONFIGS.get(asset_id)
    if config:
        return {**config, "asset_id": asset_id, "source": "backend"}
    return {"asset_id": asset_id, "signals": [], "thresholds": {}, "kpi_ids": [], "source": "backend"}


@router.get("/plants/{plant_id}/workflow-config")
def get_workflow_config(plant_id: str):
    """Simplified endpoint returning just workflow blocks."""
    if plant_id == "WTP-DEMO-01":
        return {"plant_id": plant_id, "workflow": WTP_WORKFLOW, "source": "backend"}
    return {"plant_id": plant_id, "workflow": [], "source": "backend"}
