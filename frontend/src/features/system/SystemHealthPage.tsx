import { useQuery } from "@tanstack/react-query";
import { getSystemMetrics } from "@/lib/api";
import { Database, Cpu, HardDrive } from "lucide-react";

function MetricCard({ icon: Icon, label, value, sub, color }: any) {
  return (
    <div style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }} className="rounded-lg p-5 border">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{value}</div>
          <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>{label}</div>
          {sub && <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{sub}</div>}
        </div>
      </div>
    </div>
  );
}

export function SystemHealthPage() {
  const { data: metrics } = useQuery({
    queryKey: ["system-metrics"],
    queryFn: getSystemMetrics,
    refetchInterval: 30000,
  });

  const pg = metrics?.postgresql || {};
  const td = metrics?.tdengine || {};
  const sys = metrics?.system || {};
  const totalDbSize = ((pg.size_mb || 0) + (td.size_mb || 0)).toFixed(1);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>System Health</h1>

      {/* Database Stats */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wide mb-3" style={{ color: 'var(--text-secondary)' }}>
          Database
        </h2>
        <div className="grid grid-cols-4 gap-3">
          <MetricCard
            icon={Database} label="Total DB Size" value={`${totalDbSize} MB`}
            sub={`PG: ${pg.size_mb || 0} MB · Historian: ${td.size_mb || 0} MB`}
            color="bg-cyan-500/20 text-cyan-400"
          />
          <MetricCard
            icon={Database} label="PG Records"
            value={(Object.values(pg.tables || {}) as number[]).reduce((a, b) => a + b, 0)}
            sub={Object.entries(pg.tables || {}).map(([k, v]) => `${k}: ${v}`).join(" · ")}
            color="bg-cyan-500/20 text-cyan-400"
          />
          <MetricCard
            icon={Database} label="Historian Records"
            value={(td.measurement_count || 0).toLocaleString()}
            sub={`${td.size_mb || 0} MB on disk`}
            color="bg-teal-500/20 text-teal-400"
          />
          <MetricCard
            icon={Database} label="Historian DB"
            value={td.measurement_count > 0 ? "Healthy" : "—"}
            sub={`${td.measurement_count > 0 ? 'Connected' : 'No data'}`}
            color={td.measurement_count > 0 ? "bg-green-500/20 text-green-400" : "bg-gray-500/20 text-gray-400"}
          />
        </div>
      </div>

      {/* Server Resources */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wide mb-3" style={{ color: 'var(--text-secondary)' }}>
          Server Resources
        </h2>
        <div className="grid grid-cols-3 gap-3">
          <MetricCard
            icon={Cpu} label="CPU" value={`${sys.cpu_percent || 0}%`}
            sub={`${sys.cpu_cores || 0} cores`}
            color="bg-orange-500/20 text-orange-400"
          />
          <MetricCard
            icon={Cpu} label="RAM"
            value={`${sys.ram_percent || 0}%`}
            sub={`${sys.ram_used_str || "?"} / ${sys.ram_total_str || "?"}`}
            color="bg-yellow-500/20 text-yellow-400"
          />
          <MetricCard
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
