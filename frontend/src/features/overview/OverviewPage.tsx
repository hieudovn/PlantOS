import { useQuery } from "@tanstack/react-query";
import { getAssets, getSignals, getSystemMetrics } from "@/lib/api";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { Wrench, Radio, Plug, Database, Cpu, HardDrive } from "lucide-react";

function KpiCard({ icon: Icon, label, value, sub, color }: any) {
  return (
    <div className="bg-gray-900 rounded-lg p-5 border border-gray-800">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <div className="text-2xl font-bold">{value}</div>
          <div className="text-sm text-gray-500">{label}</div>
          {sub && <div className="text-xs text-gray-600 mt-1">{sub}</div>}
        </div>
      </div>
    </div>
  );
}

export function OverviewPage() {
  const { plantId } = useWorkspace();
  const { data: assets } = useQuery({
    queryKey: ["assets", plantId],
    queryFn: () => getAssets({ plant_id: plantId }),
  });
  const { data: signals } = useQuery({
    queryKey: ["signals-all", plantId],
    queryFn: () => getSignals(),
  });
  const { data: metrics } = useQuery({
    queryKey: ["system-metrics"],
    queryFn: getSystemMetrics,
    refetchInterval: 30000,
  });

  const assetIds = new Set((assets || []).map((a: any) => a.asset_id));
  const plantSignals = (signals || []).filter((s: any) => assetIds.has(s.asset_id));

  const pg = metrics?.postgresql || {};
  const td = metrics?.tdengine || {};
  const sys = metrics?.system || {};

  const totalDbSize = ((pg.size_mb || 0) + (td.size_mb || 0)).toFixed(1);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Overview</h1>

      {/* Plant KPIs */}
      <div className="grid grid-cols-3 gap-4">
        <KpiCard icon={Wrench} label="Assets" value={assets?.length || 0} color="bg-blue-500/20 text-blue-400" />
        <KpiCard icon={Radio} label="Signals" value={plantSignals.length || 0} color="bg-purple-500/20 text-purple-400" />
        <KpiCard icon={Plug} label="Edge Nodes" value="1" color="bg-green-500/20 text-green-400" />
      </div>

      {/* Database Stats */}
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Database</h2>
        <div className="grid grid-cols-4 gap-3">
          <KpiCard
            icon={Database} label="Total Size" value={`${totalDbSize} MB`}
            sub={`PG: ${pg.size_mb || 0} MB · TD: ${td.size_mb || 0} MB`}
            color="bg-cyan-500/20 text-cyan-400"
          />
          <KpiCard
            icon={Database} label="PG Records"
            value={Object.values(pg.tables || {}).reduce((a: number, b: number) => a + b, 0)}
            sub={Object.entries(pg.tables || {}).map(([k, v]) => `${k}: ${v}`).join(" · ")}
            color="bg-cyan-500/20 text-cyan-400"
          />
          <KpiCard
            icon={Database} label="TD Measurements"
            value={(td.measurement_count || 0).toLocaleString()}
            color="bg-teal-500/20 text-teal-400"
          />
          <KpiCard
            icon={Database} label="TD Size" value={`${td.size_mb || 0} MB`}
            color="bg-teal-500/20 text-teal-400"
          />
        </div>
      </div>

      {/* Server Resources */}
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Server Resources</h2>
        <div className="grid grid-cols-3 gap-3">
          <KpiCard
            icon={Cpu} label="CPU" value={`${sys.cpu_percent || 0}%`}
            sub={`${sys.cpu_cores || 0} cores`}
            color="bg-orange-500/20 text-orange-400"
          />
          <KpiCard
            icon={Cpu} label="RAM"
            value={`${sys.ram_percent || 0}%`}
            sub={`${sys.ram_used_str || "?"} / ${sys.ram_total_str || "?"}`}
            color="bg-yellow-500/20 text-yellow-400"
          />
          <KpiCard
            icon={HardDrive} label="Disk"
            value={`${sys.disk_percent || 0}%`}
            sub={`${sys.disk_used_str || "?"} / ${sys.disk_total_str || "?"}`}
            color="bg-red-500/20 text-red-400"
          />
        </div>
      </div>
    </div>
  );
}
