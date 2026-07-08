import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCalcSignals, createCalcSignal, updateCalcSignal, deleteCalcSignal, testCalcSignal, executeCalcSignal } from "@/lib/api";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { FormulaEditor } from "./FormulaEditor";
import { StatusBadge } from "@/components/StatusBadge";
import { Plus, Pencil, Trash2, Play, FlaskConical, Loader2 } from "lucide-react";

export function CalculatedSignalsPage() {
  const queryClient = useQueryClient();
  const { plantId } = useWorkspace();
  const [showEditor, setShowEditor] = useState(false);
  const [editItem, setEditItem] = useState<any>(null);
  const [testResult, setTestResult] = useState<Record<string, any>>({});

  const { data: signals, isLoading } = useQuery({
    queryKey: ["calc-signals"],
    queryFn: () => getCalcSignals(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteCalcSignal(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["calc-signals"] }),
  });

  const testMutation = useMutation({
    mutationFn: (id: string) => testCalcSignal(id),
    onSuccess: (data, id) => setTestResult((prev) => ({ ...prev, [id]: data })),
  });

  const execMutation = useMutation({
    mutationFn: (id: string) => executeCalcSignal(id),
    onSuccess: (data, id) => {
      setTestResult((prev) => ({ ...prev, [id]: data }));
      queryClient.invalidateQueries({ queryKey: ["calc-signals"] });
    },
  });

  const saveMutation = useMutation({
    mutationFn: async (data: any) => {
      if (editItem) {
        return updateCalcSignal(editItem.calc_signal_id, data);
      } else {
        return createCalcSignal({ ...data, calc_signal_id: data.name.toLowerCase().replace(/[^a-z0-9_]/g, "_"), asset_id: plantId });
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["calc-signals"] });
      setShowEditor(false);
      setEditItem(null);
    },
  });

  if (showEditor) {
    return (
      <div className="max-w-3xl mx-auto py-6 space-y-6">
        <h1 className="text-2xl font-bold">{editItem ? "Edit" : "Create"} Calculated Signal</h1>
        <FormulaEditor
          mode={editItem ? "edit" : "create"}
          initial={editItem}
          onSave={(data) => saveMutation.mutate(data)}
          onCancel={() => { setShowEditor(false); setEditItem(null); }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Calculated Signals</h1>
        <button
          onClick={() => setShowEditor(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium"
          style={{ backgroundColor: 'var(--accent-primary)', color: '#fff' }}
        >
          <Plus className="w-4 h-4" /> Create
        </button>
      </div>

      {isLoading ? (
        <div className="text-gray-500">Loading...</div>
      ) : !signals?.length ? (
        <div className="text-center py-12" style={{ color: 'var(--text-muted)' }}>
          No calculated signals yet. Create one to define a formula.
        </div>
      ) : (
        <div className="rounded-lg border overflow-hidden" style={{ borderColor: 'var(--border-default)' }}>
          <table className="w-full text-sm">
            <thead style={{ backgroundColor: 'var(--surface-secondary)' }}>
              <tr>
                <th className="text-left px-4 py-3" style={{ color: 'var(--text-secondary)' }}>Name</th>
                <th className="text-left px-4 py-3" style={{ color: 'var(--text-secondary)' }}>Formula</th>
                <th className="text-left px-4 py-3" style={{ color: 'var(--text-secondary)' }}>Status</th>
                <th className="text-right px-4 py-3" style={{ color: 'var(--text-secondary)' }}>Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y" style={{ borderColor: 'var(--border-default)' }}>
              {signals.map((s: any) => (
                <tr key={s.calc_signal_id}>
                  <td className="px-4 py-3">
                    <div style={{ color: 'var(--text-primary)' }}>{s.display_name || s.name}</div>
                    <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{s.calc_signal_id}</div>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--text-secondary)', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {s.formula}
                    {testResult[s.calc_signal_id]?.result !== undefined && (
                      <span className="ml-2" style={{ color: '#22c55e' }}>= {testResult[s.calc_signal_id].result.toFixed(2)}</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={s.last_run_status || s.status} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => testMutation.mutate(s.calc_signal_id)}
                        className="p-1.5 rounded hover:bg-gray-700" title="Test"
                      >
                        {testMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <FlaskConical className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />}
                      </button>
                      <button
                        onClick={() => execMutation.mutate(s.calc_signal_id)}
                        className="p-1.5 rounded hover:bg-gray-700" title="Execute"
                      >
                        <Play className="w-4 h-4" style={{ color: '#22c55e' }} />
                      </button>
                      <button
                        onClick={() => { setEditItem(s); setShowEditor(true); }}
                        className="p-1.5 rounded hover:bg-gray-700" title="Edit"
                      >
                        <Pencil className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
                      </button>
                      <button
                        onClick={() => { if (confirm(`Delete "${s.name}"?`)) deleteMutation.mutate(s.calc_signal_id); }}
                        className="p-1.5 rounded hover:bg-gray-700" title="Delete"
                      >
                        <Trash2 className="w-4 h-4" style={{ color: '#ef4444' }} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
