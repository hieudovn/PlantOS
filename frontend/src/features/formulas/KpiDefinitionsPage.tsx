import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getKpis, createKpi, updateKpi, deleteKpi, testKpi } from "@/lib/api";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { FormulaEditor } from "./FormulaEditor";
import { StatusBadge } from "@/components/StatusBadge";
import { Plus, Pencil, Trash2, FlaskConical, Loader2, Eye, EyeOff } from "lucide-react";

export function KpiDefinitionsPage() {
  const queryClient = useQueryClient();
  const { plantId } = useWorkspace();
  const [showEditor, setShowEditor] = useState(false);
  const [editItem, setEditItem] = useState<any>(null);
  const [scopeFilter, setScopeFilter] = useState("plant");
  const [testResult, setTestResult] = useState<Record<string, any>>({});

  const { data: kpis, isLoading } = useQuery({
    queryKey: ["kpis", scopeFilter, plantId],
    queryFn: () => getKpis(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteKpi(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["kpis"] }),
  });

  const testMutation = useMutation({
    mutationFn: (id: string) => testKpi(id),
    onSuccess: (data, id) => setTestResult((prev) => ({ ...prev, [id]: data })),
  });

  const saveMutation = useMutation({
    mutationFn: async (data: any) => {
      if (editItem) {
        return updateKpi(editItem.kpi_id, data);
      } else {
        return createKpi({
          ...data,
          kpi_id: data.name.toLowerCase().replace(/[^a-z0-9_]/g, "_"),
          scope_type: "plant",
          scope_id: plantId,
        });
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["kpis"] });
      setShowEditor(false);
      setEditItem(null);
    },
  });

  const statusColor = (kpi: any) => {
    if (!kpi.value) return 'var(--text-muted)';
    if (kpi.critical_limit !== null && kpi.value >= kpi.critical_limit) return '#ef4444';
    if (kpi.warning_limit !== null && kpi.value >= kpi.warning_limit) return '#eab308';
    return '#22c55e';
  };

  if (showEditor) {
    return (
      <div className="max-w-3xl mx-auto py-6 space-y-6">
        <h1 className="text-2xl font-bold">{editItem ? "Edit" : "Create"} KPI Definition</h1>
        <FormulaEditor
          mode={editItem ? "edit" : "create"}
          initial={editItem}
          onSave={(data) => saveMutation.mutate(data)}
          onCancel={() => { setShowEditor(false); setEditItem(null); }}
          scope={{ type: "plant", id: plantId }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">KPI Definitions</h1>
        <button
          onClick={() => setShowEditor(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium"
          style={{ backgroundColor: 'var(--accent-primary)', color: '#fff' }}
        >
          <Plus className="w-4 h-4" /> Create
        </button>
      </div>

      {/* Scope Filter */}
      <div className="flex gap-2">
        {["plant", "area", "asset"].map((s) => (
          <button
            key={s}
            onClick={() => setScopeFilter(s)}
            className="px-3 py-1.5 rounded text-xs font-medium capitalize"
            style={{
              backgroundColor: scopeFilter === s ? 'var(--surface-hover)' : 'transparent',
              color: scopeFilter === s ? 'var(--text-primary)' : 'var(--text-muted)',
              border: `1px solid ${scopeFilter === s ? 'var(--border-default)' : 'transparent'}`,
            }}
          >
            {s}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="text-gray-500">Loading...</div>
      ) : !kpis?.length ? (
        <div className="text-center py-12" style={{ color: 'var(--text-muted)' }}>
          No KPI definitions yet for this scope.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {kpis.map((kpi: any) => (
            <div
              key={kpi.kpi_id}
              className="rounded-lg p-4 border"
              style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }}
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{kpi.display_name || kpi.name}</div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{kpi.kpi_id}</div>
                </div>
                <StatusBadge status={kpi.status} />
              </div>

              <div className="text-xs font-mono mb-2 truncate" style={{ color: 'var(--text-secondary)' }}>
                {kpi.formula}
              </div>

              {testResult[kpi.kpi_id]?.result !== undefined && (
                <div className="text-2xl font-bold mb-2" style={{ color: statusColor({ ...kpi, value: testResult[kpi.kpi_id].result }) }}>
                  {testResult[kpi.kpi_id].result.toFixed(1)}
                  {kpi.unit && <span className="text-sm ml-1" style={{ color: 'var(--text-muted)' }}>{kpi.unit}</span>}
                </div>
              )}

              {kpi.target !== null && kpi.target !== undefined && (
                <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  Target: {kpi.target} {kpi.unit || ""}
                </div>
              )}

              <div className="flex items-center gap-1 mt-3">
                <button
                  onClick={() => testMutation.mutate(kpi.kpi_id)}
                  className="p-1.5 rounded hover:bg-gray-700" title="Test"
                >
                  {testMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FlaskConical className="w-3.5 h-3.5" style={{ color: 'var(--text-secondary)' }} />}
                </button>
                <button
                  onClick={() => { setEditItem(kpi); setShowEditor(true); }}
                  className="p-1.5 rounded hover:bg-gray-700" title="Edit"
                >
                  <Pencil className="w-3.5 h-3.5" style={{ color: 'var(--text-secondary)' }} />
                </button>
                <button
                  onClick={() => { if (confirm(`Delete "${kpi.name}"?`)) deleteMutation.mutate(kpi.kpi_id); }}
                  className="p-1.5 rounded hover:bg-gray-700" title="Delete"
                >
                  <Trash2 className="w-3.5 h-3.5" style={{ color: '#ef4444' }} />
                </button>
                <span className="text-xs ml-auto" style={{ color: 'var(--text-muted)' }}>
                  {kpi.show_in_process_view ? <Eye className="w-3 h-3 inline" /> : <EyeOff className="w-3 h-3 inline" />}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
