import ReactECharts from "echarts-for-react";
import { useQueries } from "@tanstack/react-query";
import { getHistory } from "@/lib/api";

const COLORS = ["#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6", "#ef4444", "#06b6d4", "#f97316", "#ec4899"];

type Props = { signalIds: string[]; from: string; to: string };

export function TrendChart({ signalIds, from, to }: Props) {
  const queries = useQueries({
    queries: signalIds.map(sid => ({
      queryKey: ["history", sid, from, to],
      queryFn: () => getHistory({ signal_id: sid, from, to }),
      enabled: !!sid && !!from && !!to,
    })),
  });

  if (signalIds.length === 0) {
    return <div className="text-gray-600 text-center py-16">Add signals to view trends</div>;
  }

  if (!queries.every(q => !q.isLoading)) {
    return <div className="text-gray-500 py-8">Loading...</div>;
  }

  const series: any[] = [];
  signalIds.forEach((sid, i) => {
    const data = queries[i]?.data;
    const points = data?.data || [];
    if (points.length === 0) return;
    const good = points.filter((p: any) => !p.quality || p.quality === "GOOD");
    const bad = points.filter((p: any) => p.quality && p.quality !== "GOOD");
    series.push({
      name: sid,
      type: "line",
      data: good.map((p: any) => [p.timestamp, p.value]),
      smooth: false,
      symbol: "none",
      lineStyle: { color: COLORS[i % COLORS.length], width: 1.5 },
    });
    if (bad.length > 0) {
      series.push({
        name: `${sid} (bad)`,
        type: "scatter",
        data: bad.map((p: any) => [p.timestamp, p.value]),
        symbolSize: 8,
        itemStyle: { color: COLORS[i % COLORS.length], opacity: 0.4 },
      });
    }
  });

  const total = queries.reduce((s, q) => s + (q.data?.data?.length || 0), 0);

  const option = {
    backgroundColor: "transparent",
    legend: {
      data: signalIds,
      bottom: 0,
      textStyle: { color: "#9ca3af", fontSize: 11 },
    },
    grid: { top: 20, right: 40, bottom: 40, left: 70 },
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
    },
    series,
  };

  return (
    <div>
      <div className="text-xs text-gray-500 mb-2">{total} data points</div>
      <ReactECharts option={option} style={{ height: 400 }} notMerge />
    </div>
  );
}
