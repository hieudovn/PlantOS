import ReactECharts from "echarts-for-react";
import { useQueries } from "@tanstack/react-query";
import { getHistory } from "@/lib/api";

const COLORS = ["#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6", "#ef4444", "#06b6d4", "#f97316", "#ec4899"];

type Props = { signalIds: string[]; from: string; to: string; chartType?: string; height?: number; compact?: boolean; refetchInterval?: number };

export function TrendChart({ signalIds, from, to, chartType = "line" }: Props) {
  // Normalize timestamps: datetime-local inputs may store UTC ISO strings
  // internally (e.g. "2026-06-30T17:00:00.000Z") while displaying local time.
  // Convert to local format (YYYY-MM-DDTHH:mm) to ensure TDengine query uses
  // the correct calendar date.
  const toLocalFormat = (ts: string): string => {
    // Pass through local time as-is — API + data both use VN timezone (+07:00)
    return ts;
  };
  const localFrom = toLocalFormat(from);
  const localTo = toLocalFormat(to);

  const queries = useQueries({
    queries: signalIds.map(sid => ({
      queryKey: ["history", sid, localFrom, localTo],
      queryFn: () => getHistory({ signal_id: sid, from: localFrom, to: localTo }),
      enabled: !!sid && !!localFrom && !!localTo,
      refetchInterval: 5000,
    })),
  });

  if (signalIds.length === 0) {
    return <div className="text-gray-600 text-center py-16">Add signals to view trends</div>;
  }

  if (!queries.every(q => !q.isLoading)) {
    return <div className="text-gray-500 py-8">Loading...</div>;
  }

  const toLocalTs = (ts: string): string => {
    // Backend stores VN time but returns with Z suffix. Convert for display.
    if (ts.endsWith("Z")) return ts.slice(0, -1) + "+07:00";
    return ts;
  };

  const series: any[] = [];
  signalIds.forEach((sid, i) => {
    const data = queries[i]?.data;
    const points = data?.data || [];
    if (points.length === 0) return;
    const VALID_QUALITIES = new Set(["GOOD", "SIMULATED", "ESTIMATED"]);
    const good = points.filter((p: any) => !p.quality || VALID_QUALITIES.has(p.quality));
    const bad = points.filter((p: any) => p.quality && !VALID_QUALITIES.has(p.quality));
    const echartsType = chartType === "area" ? "line" : chartType;
    series.push({
      name: sid,
      type: echartsType,
      data: good.map((p: any) => [toLocalTs(p.timestamp), p.value]),
      smooth: false,
      symbol: chartType === "scatter" ? "circle" : chartType === "bar" ? "none" : "circle",
      symbolSize: chartType === "scatter" ? 8 : 4,
      lineStyle: chartType === "scatter" ? undefined : { color: COLORS[i % COLORS.length], width: 1.5 },
      itemStyle: { color: COLORS[i % COLORS.length] },
      areaStyle:
        chartType === "area"
          ? { color: COLORS[i % COLORS.length] + "18", opacity: 0.3 }
          : undefined,
      barMaxWidth: 20,
    });
    if (bad.length > 0) {
      series.push({
        name: `${sid} (bad)`,
        type: "scatter",
        data: bad.map((p: any) => [toLocalTs(p.timestamp), p.value]),
        symbolSize: 8,
        itemStyle: { color: COLORS[i % COLORS.length], opacity: 0.4 },
      });
    }
  });

  const total = queries.reduce((s, q) => s + (q.data?.data?.length || 0), 0);

  if (series.length === 0 && total === 0 && signalIds.length > 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-500">
        No data found for this time range
      </div>
    );
  }

  const option = {
    backgroundColor: "transparent",
    legend: {
      data: signalIds,
      top: 0,
      left: "center",
      textStyle: { color: "#9ca3af", fontSize: 11 },
    },
    grid: { top: 35, right: 40, bottom: 90, left: 70 },
    toolbox: {
      feature: {
        restore: { title: "Reset", iconStyle: { borderColor: "#9ca3af" } },
        saveAsImage: { title: "Save", backgroundColor: "#0f172a" },
        dataZoom: { title: { zoom: "Zoom", back: "Back" }, iconStyle: { borderColor: "#9ca3af" } },
      },
      right: 10,
      top: 5,
      iconStyle: { borderColor: "#9ca3af" },
    },
    dataZoom: [
      {
        type: "slider",
        start: 0,
        end: 100,
        bottom: 30,
        height: 20,
        borderColor: "#374151",
        backgroundColor: "#1e293b",
        fillerColor: "rgba(59,130,246,0.15)",
        handleStyle: { color: "#3b82f6" },
        textStyle: { color: "#9ca3af", fontSize: 10 },
      },
      {
        type: "inside",
        start: 0,
        end: 100,
        zoomOnMouseWheel: true,
        moveOnMouseMove: true,
      },
    ],
    xAxis: {
      type: "time",
      axisLine: { lineStyle: { color: "#374151" } },
      axisLabel: { color: "#9ca3af", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      axisLine: { lineStyle: { color: "#374151" } },
      axisLabel: { color: "#9ca3af", fontSize: 11 },
      splitLine: { lineStyle: { color: "#1f2937" } },
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#1f2937",
      borderColor: "#374151",
      textStyle: { color: "#e5e7eb", fontSize: 12 },
      axisPointer: {
        type: "cross",
        crossStyle: { color: "#6b7280" },
        label: { backgroundColor: "#1f2937", color: "#e5e7eb" },
      },
    },
    series,
  };

  return (
    <div>
      <div className="text-xs text-gray-500 mb-2">{total} data points</div>
      <ReactECharts option={option} style={{ height: 500 }} notMerge opts={{ renderer: "canvas" }} />
    </div>
  );
}
