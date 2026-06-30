import { useQuery } from "@tanstack/react-query";
import { getAssets, getSignals } from "@/lib/api";
import { Wrench, Radio, Plug } from "lucide-react";

function KpiCard({ icon: Icon, label, value, color }: any) {
  return (
    <div className="bg-gray-900 rounded-lg p-5 border border-gray-800">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <div className="text-2xl font-bold">{value}</div>
          <div className="text-sm text-gray-500">{label}</div>
        </div>
      </div>
    </div>
  );
}

export function OverviewPage() {
  const { data: assets } = useQuery({ queryKey: ["assets"], queryFn: () => getAssets() });
  const { data: signals } = useQuery({ queryKey: ["signals-all"], queryFn: () => getSignals() });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Overview</h1>
      <div className="grid grid-cols-3 gap-4">
        <KpiCard icon={Wrench} label="Assets" value={assets?.length || 0} color="bg-blue-500/20 text-blue-400" />
        <KpiCard icon={Radio} label="Signals" value={signals?.length || 0} color="bg-purple-500/20 text-purple-400" />
        <KpiCard icon={Plug} label="Edge Nodes" value="1" color="bg-green-500/20 text-green-400" />
      </div>
    </div>
  );
}
