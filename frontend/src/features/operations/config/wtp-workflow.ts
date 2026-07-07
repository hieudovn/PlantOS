import { ProcessBlockConfig } from "../components/ProcessBlock";

export const WTP_WORKFLOW: ProcessBlockConfig[] = [
  {
    id: "intake",
    label: "Intake",
    areaId: "INTAKE-AREA",
    signalId: "RWP-101.flow_rate",
    unit: "m³/h",
  },
  {
    id: "dosing",
    label: "Dosing",
    areaId: "CHEMICAL-DOSING-AREA",
    signalId: "CHEMICAL-CONSUMPTION-STATION-101.coagulant_dose_rate",
    unit: "mg/L",
  },
  {
    id: "clarifier",
    label: "Clarifier",
    areaId: "CLARIFICATION-AREA",
    signalId: "CLARIFIER-101.settled_turbidity",
    unit: "NTU",
  },
  {
    id: "filters",
    label: "Filters",
    areaId: "FILTRATION-AREA",
    signalId: "FILTER-QUALITY-STATION-101.filtered_turbidity",
    unit: "NTU",
  },
  {
    id: "disinfection",
    label: "Disinfection",
    areaId: "DISINFECTION-CLEARWATER-AREA",
    signalId: "DISINFECTION-QUALITY-STATION-101.free_chlorine",
    unit: "mg/L",
  },
  {
    id: "storage",
    label: "Storage",
    areaId: "DISINFECTION-CLEARWATER-AREA",
    signalId: "CLEAR-WATER-TANK-101.level",
    unit: "%",
  },
  {
    id: "distribution",
    label: "Distribution",
    areaId: "DISTRIBUTION-AREA",
    signalId: "HSP-101.flow_rate",
    unit: "m³/h",
  },
];