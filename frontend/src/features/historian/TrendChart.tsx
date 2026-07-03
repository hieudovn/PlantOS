import ReactECharts from "echarts-for-react";
import { useQueries } from "@tanstack/react-query";
import { getHistory } from "@/lib/api";

const COLORS = ["#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6", "#ef4444", "#06b6d4", "#f97316", "#ec4899"];

type Props = { signalIds: string[]; from: string; to: string; chartType?: string; showLegend?: boolean; showToolbox?: boolean; refetchInterval?: number; height?: number; compact?: boolean };

export function TrendChart({ signalIds, from, to, chartType = "line", showLegend = true, showToolbox = true, refetchInterval = 5000, height = 500, compact = false }: Props) {
  const queries = useQueries({
    queries: signalIds.map(sid => ({
      queryKey: ["history", sid, from, to],
      queryFn: () => getHistory({ signal_id: sid, from, to }),
      enabled: !!sid && !!from && !!to,
      refetchInterval,
    })),
  });

  if (signalIds.length === 0) {
    return <div className="text-gray-600 text-center py-16">Add signals to view trends</div>;
  }

  if (!queries.every(q => !q.isLoading)) {
    return <div className="text-gray-500 py-8">Loading...</div>;
  }

  const toLocalTs = (ts: string): string => {
    const d = new Date(ts);
    if (!isNaN(d.getTime())) {
      const y = d.getFullYear();
      const mo = String(d.getMonth() + 1).padStart(2, "0");
      const dd = String(d.getDate()).padStart(2, "0");
      const h = String(d.getHours()).padStart(2, "0");
      const mi = String(d.getMinutes()).padStart(2, "0");
      const s = String(d.getSeconds()).padStart(2, "0");
      return `${y}-${mo}-${dd}T${h}:${mi}:${s}`;
    }
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
      areaStyle: chartType === "area" ? { color: COLORS[i % COLORS.length] + "18", opacity: 0.3 } : undefined,
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
    ...(showLegend ? {
      legend: {
        data: signalIds,
        top: 0,
        left: "center",
        textStyle: { color: "#9ca3af", fontSize: 11 },
      },
    } : {}),
    grid: { top: compact ? 5 : (showLegend ? 35 : showToolbox ? 35 : 5), right: compact ? 10 : (showToolbox ? 40 : 15), bottom: compact ? 20 : (showToolbox ? 30 : 5), left: compact ? 45 : 55 },
    ...(showToolbox && !compact ? {
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
    } : {}),
    dataZoom: !compact ? [
      ...(showToolbox ? [{
        type: "slider",
        start: 0, end: 100, bottom: 30, height: 20,
        borderColor: "#374151", backgroundColor: "#1e293b",
        fillerColor: "rgba(59,130,246,0.15)", handleStyle: { color: "#3b82f6" },
        textStyle: { color: "#9ca3af", fontSize: 10 },
      }] : []),
      { type: "inside", start: 0, end: 100, zoomOnMouseWheel: true, moveOnMouseMove: true },
    ] : [
      { type: "inside", start: 0, end: 100, zoomOnMouseWheel: false, moveOnMouseMove: false },
    ],
    xAxis: {
      type: "time",
      axisLine: { lineStyle: { color: "#374151" } },
      axisLabel: { color: "#9ca3af", fontSize: compact ? 10 : 11 },
    },
    yAxis: {
      type: "value",
      axisLine: { lineStyle: { color: "#374151" } },
      axisLabel: { color: "#9ca3af", fontSize: compact ? 10 : 11 },
      splitLine: { lineStyle: { color: "#1f2937" } },
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#1f2937",
      borderColor: "#374151",
      textStyle: { color: "#e5e7eb", fontSize: 12 },
    },
    series,
  };

  return (
    <div style={{ overflow: "hidden", height: compact ? height : "auto" }}>
      {!compact && <div className="text-xs text-gray-500 mb-2">{total} data points</div>}
      <ReactECharts option={option} style={{ height: compact ? height : height, overflow: "hidden" }} notMerge opts={{ renderer: "canvas" }} />
    </div>
  );
}
