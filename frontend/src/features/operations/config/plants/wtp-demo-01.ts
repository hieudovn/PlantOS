import { PlantConfig } from "../types";

/**
 * WTP-DEMO-01 plant config.
 * Signal and area IDs verified against live API data.
 */
export const wtpDemo01Config: PlantConfig = {
  workflow: [
    { id: "intake", label: "Intake", areaId: "INTAKE-AREA", signalId: "RWP-101.flow_rate", unit: "m³/h" },
    { id: "dosing", label: "Dosing", areaId: "CHEMICAL-DOSING-AREA", signalId: "CHEMICAL-CONSUMPTION-STATION-101.coagulant_dose_rate", unit: "mg/L" },
    { id: "clarifier", label: "Clarifier", areaId: "CLARIFICATION-AREA", signalId: "CLARIFIER-101.settled_turbidity", unit: "NTU" },
    { id: "filters", label: "Filters", areaId: "FILTRATION-AREA", signalId: "FILTER-QUALITY-STATION-101.filtered_turbidity", unit: "NTU" },
    { id: "disinfection", label: "Disinfection", areaId: "DISINFECTION-CLEARWATER-AREA", signalId: "DISINFECTION-QUALITY-STATION-101.free_chlorine", unit: "mg/L" },
    { id: "storage", label: "Storage", areaId: "DISINFECTION-CLEARWATER-AREA", signalId: "CLEAR-WATER-TANK-101.level", unit: "%" },
    { id: "distribution", label: "Distribution", areaId: "DISTRIBUTION-AREA", signalId: "HSP-101.flow_rate", unit: "m³/h" },
  ],
  assetSignals: {
    "FILTER-101": [
      { signalId: "FILTER-101.filter_dp", label: "DP", unit: "kPa" },
      { signalId: "FILTER-101.effluent_flow", label: "Effluent", unit: "m³/h" },
    ],
    "FILTER-102": [
      { signalId: "FILTER-102.filter_dp", label: "DP", unit: "kPa" },
      { signalId: "FILTER-102.effluent_flow", label: "Effluent", unit: "m³/h" },
    ],
    "BACKWASH-PUMP-101": [
      { signalId: "BACKWASH-PUMP-101.running_status", label: "Status", unit: "" },
    ],
    "FILTER-QUALITY-STATION-101": [
      { signalId: "FILTER-QUALITY-STATION-101.filtered_turbidity", label: "Turbidity", unit: "NTU" },
      { signalId: "FILTER-QUALITY-STATION-101.filter_run_quality_index", label: "Quality", unit: "" },
    ],
  },
  thresholds: {
    "RWP-101.flow_rate": { warn: 400, crit: 200, direction: "low" },
    "CHEMICAL-CONSUMPTION-STATION-101.coagulant_dose_rate": { warn: 50, crit: 80, direction: "high" },
    "CLARIFIER-101.settled_turbidity": { warn: 5, crit: 10, direction: "high" },
    "FILTER-QUALITY-STATION-101.filtered_turbidity": { warn: 0.5, crit: 1, direction: "high" },
    "DISINFECTION-QUALITY-STATION-101.free_chlorine": { warn: 0.8, crit: 0.5, direction: "low" },
    "CLEAR-WATER-TANK-101.level": { warn: 30, crit: 15, direction: "low" },
    "HSP-101.flow_rate": { warn: 300, crit: 150, direction: "low" },
    "FILTER-101.filter_dp": { warn: 60, crit: 80, direction: "high" },
    "FILTER-102.filter_dp": { warn: 60, crit: 80, direction: "high" },
  },
};
