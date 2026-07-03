import { useQuery } from "@tanstack/react-query";
import { getAssets, getSignals, getHistory, getAlarms } from "@/lib/api";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { KpiCard } from "@/components/industrial/KpiCard";
import { WorkflowDiagram } from "@/components/diagrams/WorkflowDiagram";
import { Circle, TrendingUp, TrendingDown, Minus, ExternalLink } from "lucide-react";

function useLatestValue(signalId: string) {
  return useQuery({
    queryKey: ["current", signalId],
    queryFn: () =>
      getHistory({ signal_id: signalId, from: "2026-07-01T00:00:00.000Z", to: new Date().toISOString() }).then((res: any) => {
        const data = res?.data || [];
        return data.length > 0 ? data[data.length - 1] : null;
      }),
    refetchInterval: 10000,
    enabled: !!signalId,
  });
}

function formatNum(n: number, decimals = 2): string {
  if (n === undefined || n === null) return "—";
  if (Math.abs(n) >= 1000) return n.toFixed(0);
  if (Math.abs(n) >= 1) return n.toFixed(decimals);
  return n.toFixed(decimals);
}

function QuickValue({ label, value, unit, status, signalId }: {
  label: string; value: string; unit?: string; status?: "normal" | "warning" | "critical"; signalId: string;
}) {
  const statusColor = status === "critical" ? "var(--status-critical)" : status === "warning" ? "var(--status-warning)" : "var(--status-normal)";
  return (
    <div className="flex items-center justify-between py-1.5 border-b last:border-b-0" style={{ borderColor: 'var(--border-subtle)' }}>
      <div className="flex items-center gap-2">
        <Circle className="w-2 h-2 fill-current" style={{ color: statusColor }} />
        <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs font-mono font-bold" style={{ color: 'var(--text-primary)' }}>{value}</span>
        {unit && <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{unit}</span>}
        <a href={`/historian?signal=${signalId}`} className="text-xs opacity-50 hover:opacity-100" style={{ color: 'var(--accent-primary)' }} title="Open in Historian">
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </div>
  );
}

export function OverviewPage() {
  const { plantId } = useWorkspace();
  const isWtp = plantId === "WTP-DEMO-01";

  const { data: assets } = useQuery({
    queryKey: ["assets", plantId],
    queryFn: () => getAssets({ plant_id: plantId }),
  });
  const { data: signals } = useQuery({
    queryKey: ["signals-all", plantId],
    queryFn: () => getSignals({ plant_id: plantId }),
  });
  const { data: alarms } = useQuery({
    queryKey: ["alarms-active"],
    queryFn: () => getAlarms({ state: "active" }),
    refetchInterval: 15000,
  });

  const flow = useLatestValue(isWtp ? "OUTLET-MANIFOLD-101.manifold_flow" : "");
  const outletCompliance = useLatestValue(isWtp ? "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_compliance_status" : "");
  const outletQuality = useLatestValue(isWtp ? "PLANT-KPI-101.outlet_quality_index" : "");
  const costPerM3 = useLatestValue(isWtp ? "PLANT-KPI-101.cost_per_m3" : "");

  const rawTurb = useLatestValue(isWtp ? "RAW-WATER-QUALITY-STATION-101.raw_turbidity" : "");
  const settTurb = useLatestValue(isWtp ? "CLARIFIER-101.settled_turbidity" : "");
  const filtTurb = useLatestValue(isWtp ? "FILTER-QUALITY-STATION-101.filtered_turbidity" : "");
  const filtDp = useLatestValue(isWtp ? "FILTER-101.filter_dp" : "");
  const freeCl = useLatestValue(isWtp ? "DISINFECTION-QUALITY-STATION-101.free_chlorine" : "");
  const outletFlow = useLatestValue(isWtp ? "HSP-101.flow_rate" : "");
  const outletTurb = useLatestValue(isWtp ? "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity" : "");
  const energy = useLatestValue(isWtp ? "ENERGY-MONITORING-STATION-101.specific_energy_consumption" : "");

  const activeAlarms = (alarms || []).length;
  const assetCount = assets?.length || 0;
  const healthState = activeAlarms > 0 ? (activeAlarms > 3 ? "critical" : "warning") : "normal";

  const stages = isWtp ? [
    { id: "intake", label: "Intake", status: (rawTurb.data?.value ?? 0) > 80 ? "warning" as const : "normal" as const,
      kpis: [{ label: "Turbidity", value: rawTurb.data?.value !== undefined ? formatNum(rawTurb.data.value) : "—", unit: "NTU" }] },
    { id: "dosing", label: "Dosing", status: "normal" as const,
      kpis: [{ label: "Cl₂ Residual", value: freeCl.data?.value !== undefined ? formatNum(freeCl.data.value, 1) : "—", unit: "mg/L" }] },
    { id: "clarification", label: "Clarifier", status: (settTurb.data?.value ?? 0) > 10 ? "warning" as const : "normal" as const,
      kpis: [{ label: "Turbidity", value: settTurb.data?.value !== undefined ? formatNum(settTurb.data.value) : "—", unit: "NTU" }] },
    { id: "filtration", label: "Filters", status: (filtDp.data?.value ?? 0) > 80 ? "critical" as const : (filtDp.data?.value ?? 0) > 60 ? "warning" as const : "normal" as const,
      kpis: [{ label: "Turbidity", value: filtTurb.data?.value !== undefined ? formatNum(filtTurb.data.value) : "—", unit: "NTU" }, { label: "DP", value: filtDp.data?.value !== undefined ? formatNum(filtDp.data.value) : "—", unit: "kPa" }] },
    { id: "disinfection", label: "Disinfection", status: (freeCl.data?.value ?? 0) < 0.5 ? "critical" as const : (freeCl.data?.value ?? 0) < 0.8 ? "warning" as const : "normal" as const,
      kpis: [{ label: "Free Cl₂", value: freeCl.data?.value !== undefined ? formatNum(freeCl.data.value, 1) : "—", unit: "mg/L" }] },
    { id: "distribution", label: "Distribution", status: "normal" as const,
      kpis: [{ label: "Flow", value: outletFlow.data?.value !== undefined ? formatNum(outletFlow.data.value, 0) : "—", unit: "m³/h" }] },
  ] : [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Operations Cockpit</h1>
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{plantId}</span>
      </div>

      {/* ROW 1: KPI Cards */}
      <div className="grid grid-cols-5 gap-3">
        <KpiCard label="Plant Health" value={healthState === "normal" ? "Operational" : `${activeAlarms} alarms`} state={healthState} />
        <KpiCard label="Production" value={isWtp ? (flow.data?.value ? formatNum(flow.data.value, 0) : "—") : "—"} unit="m³/h" quality="GOOD" timestamp={flow.data?.timestamp || undefined} trend="up" trendLabel="+2.1% vs yesterday" />
        <KpiCard label="Water Quality" value={isWtp && outletQuality.data ? formatNum(outletQuality.data.value) : "—"} unit="index" quality="GOOD" timestamp={outletQuality.data?.timestamp || undefined} state={outletCompliance.data?.value === false ? "critical" : undefined} />
        <KpiCard label="Cost" value={isWtp && costPerM3.data ? formatNum(costPerM3.data.value, 0) : "—"} unit="VND/m³" quality="GOOD" timestamp={costPerM3.data?.timestamp || undefined} />
        <KpiCard label="Active Alarms" value={activeAlarms} state={activeAlarms > 0 ? (activeAlarms > 3 ? "critical" : "warning") : "normal"} quality={activeAlarms > 0 ? "BAD" : "GOOD"} />
      </div>

      {/* ROW 2: Workflow + Incidents */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-8">
          {isWtp ? <WorkflowDiagram stages={stages} plantId={plantId} /> : (
            <div style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }} className="rounded-lg border p-6">
              <h3 className="text-xs font-semibold uppercase tracking-wide mb-3" style={{ color: 'var(--text-secondary)' }}>Process Overview</h3>
              <div className="grid grid-cols-3 gap-3">
                <KpiCard label="Assets" value={assetCount} /><KpiCard label="Signals" value={(signals || []).length} /><KpiCard label="Edge Nodes" value="1" />
              </div>
            </div>
          )}
        </div>
        <div className="col-span-4">
          <div style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }} className="rounded-lg border p-4 h-full">
            <h3 className="text-xs font-semibold uppercase tracking-wide mb-3" style={{ color: 'var(--text-secondary)' }}>Active Incidents</h3>
            {activeAlarms === 0 ? (
              <div className="flex flex-col items-center justify-center py-8" style={{ color: 'var(--text-muted)' }}>
                <Circle className="w-6 h-6 mb-2" style={{ color: 'var(--status-normal)' }} />
                <span className="text-xs">No active incidents</span>
              </div>
            ) : (
              <div className="space-y-2">{/* alarm list here */}</div>
            )}
          </div>
        </div>
      </div>

      {/* ROW 3: Quick Values — instant readings with warnings, link to Historian */}
      {isWtp && (
        <div className="grid grid-cols-2 gap-4">
          <div style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }} className="rounded-lg border p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Water Quality</h3>
              <a href="/historian" className="text-xs flex items-center gap-1 hover:underline" style={{ color: 'var(--accent-primary)' }}>
                Historian <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            <QuickValue label="Raw Turbidity" value={rawTurb.data?.value !== undefined ? formatNum(rawTurb.data.value) : "—"} unit="NTU"
              status={(rawTurb.data?.value ?? 0) > 80 ? "critical" : (rawTurb.data?.value ?? 0) > 50 ? "warning" : "normal"}
              signalId="RAW-WATER-QUALITY-STATION-101.raw_turbidity" />
            <QuickValue label="Settled Turbidity" value={settTurb.data?.value !== undefined ? formatNum(settTurb.data.value) : "—"} unit="NTU"
              status={(settTurb.data?.value ?? 0) > 10 ? "critical" : (settTurb.data?.value ?? 0) > 5 ? "warning" : "normal"}
              signalId="CLARIFIER-101.settled_turbidity" />
            <QuickValue label="Filtered Turbidity" value={filtTurb.data?.value !== undefined ? formatNum(filtTurb.data.value) : "—"} unit="NTU"
              status={(filtTurb.data?.value ?? 0) > 1 ? "critical" : (filtTurb.data?.value ?? 0) > 0.5 ? "warning" : "normal"}
              signalId="FILTER-QUALITY-STATION-101.filtered_turbidity" />
            <QuickValue label="Outlet Turbidity" value={outletTurb.data?.value !== undefined ? formatNum(outletTurb.data.value) : "—"} unit="NTU"
              status={(outletTurb.data?.value ?? 0) > 1 ? "critical" : (outletTurb.data?.value ?? 0) > 0.5 ? "warning" : "normal"}
              signalId="TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity" />
            <QuickValue label="Free Chlorine" value={freeCl.data?.value !== undefined ? formatNum(freeCl.data.value, 1) : "—"} unit="mg/L"
              status={(freeCl.data?.value ?? 0) < 0.5 ? "critical" : (freeCl.data?.value ?? 0) < 0.8 ? "warning" : "normal"}
              signalId="DISINFECTION-QUALITY-STATION-101.free_chlorine" />
            <QuickValue label="Filter DP" value={filtDp.data?.value !== undefined ? formatNum(filtDp.data.value) : "—"} unit="kPa"
              status={(filtDp.data?.value ?? 0) > 80 ? "critical" : (filtDp.data?.value ?? 0) > 60 ? "warning" : "normal"}
              signalId="FILTER-101.filter_dp" />
          </div>
          <div style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }} className="rounded-lg border p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Energy & Cost</h3>
              <a href="/historian" className="text-xs flex items-center gap-1 hover:underline" style={{ color: 'var(--accent-primary)' }}>
                Historian <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            <QuickValue label="Production Flow" value={flow.data?.value !== undefined ? formatNum(flow.data.value, 0) : "—"} unit="m³/h"
              signalId="OUTLET-MANIFOLD-101.manifold_flow" />
            <QuickValue label="Specific Energy" value={energy.data?.value !== undefined ? formatNum(energy.data.value) : "—"} unit="kWh/m³"
              status={(energy.data?.value ?? 0) > 0.5 ? "warning" : "normal"}
              signalId="ENERGY-MONITORING-STATION-101.specific_energy_consumption" />
            <QuickValue label="Energy Cost" value={costPerM3.data?.value !== undefined ? formatNum(costPerM3.data.value, 0) : "—"} unit="VND/m³"
              signalId="PLANT-KPI-101.cost_per_m3" />
            <QuickValue label="Chemical Cost" value={"—"} unit="VND/m³"
              signalId="CHEMICAL-CONSUMPTION-STATION-101.chemical_cost_per_m3"
              status="normal" />
            <QuickValue label="Quality Index" value={outletQuality.data?.value !== undefined ? formatNum(outletQuality.data.value) : "—"}
              status={(outletQuality.data?.value ?? 10) < 5 ? "warning" : "normal"}
              signalId="PLANT-KPI-101.outlet_quality_index" />
            <QuickValue label="Compliance" value={outletCompliance.data?.value === false ? "FAIL" : outletCompliance.data?.value === true ? "PASS" : "—"}
              status={outletCompliance.data?.value === false ? "critical" : "normal"}
              signalId="TRANSFER-OUTLET-QUALITY-STATION-101.outlet_compliance_status" />
          </div>
        </div>
      )}
    </div>
  );
}
