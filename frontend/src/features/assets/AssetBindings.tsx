import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getBindings, createBinding, deleteBinding, validateBindings, getSignals } from "@/lib/api";
import { Loader2, CheckCircle, AlertTriangle, XCircle, Link2, Unlink } from "lucide-react";

interface AssetBindingsProps {
  assetId: string;
}

export function AssetBindings({ assetId }: AssetBindingsProps) {
  const queryClient = useQueryClient();
  const [bindingSignal, setBindingSignal] = useState<{ attr: string; open: boolean } | null>(null);
  const [signalSearch, setSignalSearch] = useState("");

  const { data: bindings, isLoading } = useQuery({
    queryKey: ["bindings", assetId],
    queryFn: () => getBindings(assetId),
  });

  const { data: allSignals } = useQuery({
    queryKey: ["signals-all"],
    queryFn: () => getSignals(),
  });

  const validateMutation = useMutation({
    mutationFn: () => validateBindings(assetId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["bindings", assetId] }),
  });

  const bindMutation = useMutation({
    mutationFn: ({ attr, signalId }: { attr: string; signalId: string }) =>
      createBinding({ asset_id: assetId, attribute_name: attr, signal_id: signalId, binding_type: "direct" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bindings", assetId] });
      setBindingSignal(null);
    },
  });

  const unbindMutation = useMutation({
    mutationFn: (bindingId: string) => deleteBinding(bindingId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["bindings", assetId] }),
  });

  const filteredSignals = allSignals?.filter((s: any) =>
    !signalSearch ||
    s.signal_id.toLowerCase().includes(signalSearch.toLowerCase()) ||
    s.display_name?.toLowerCase().includes(signalSearch.toLowerCase())
  );

  const statusIcon = (status: string | null) => {
    switch (status) {
      case "ok": return <CheckCircle className="w-4 h-4" style={{ color: "#22c55e" }} />;
      case "warning": return <AlertTriangle className="w-4 h-4" style={{ color: "#eab308" }} />;
      case "error": return <XCircle className="w-4 h-4" style={{ color: "#ef4444" }} />;
      default: return <span className="w-4 h-4 inline-block" style={{ color: 'var(--text-muted)' }}>—</span>;
    }
  };

  if (isLoading) return <div className="text-gray-500 py-4">Loading bindings...</div>;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Signals / Attributes</h2>
        <button
          onClick={() => validateMutation.mutate()}
          disabled={validateMutation.isPending}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm"
          style={{ backgroundColor: 'var(--surface-hover)', color: 'var(--text-secondary)' }}
        >
          {validateMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
          Validate
        </button>
      </div>

      {/* Validation summary */}
      {validateMutation.data && (
        <div
          className="p-3 rounded text-sm"
          style={{
            backgroundColor: validateMutation.data.valid ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
            border: `1px solid ${validateMutation.data.valid ? "rgba(34,197,94,0.3)" : "rgba(239,68,68,0.3)"}`,
            color: validateMutation.data.valid ? "#22c55e" : "#ef4444",
          }}
        >
          {validateMutation.data.valid
            ? "All bindings are valid"
            : `${validateMutation.data.errors.length} error(s), ${validateMutation.data.warnings.length} warning(s)`
          }
        </div>
      )}

      {/* Bindings table */}
      <div className="rounded-lg border overflow-hidden" style={{ borderColor: 'var(--border-default)' }}>
        <table className="w-full text-sm">
          <thead style={{ backgroundColor: 'var(--surface-secondary)' }}>
            <tr>
              <th className="text-left px-4 py-2.5" style={{ color: 'var(--text-secondary)' }}>Attribute</th>
              <th className="text-left px-4 py-2.5" style={{ color: 'var(--text-secondary)' }}>Bound Signal</th>
              <th className="text-center px-4 py-2.5" style={{ color: 'var(--text-secondary)' }}>Status</th>
              <th className="text-right px-4 py-2.5" style={{ color: 'var(--text-secondary)' }}>Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y" style={{ borderColor: 'var(--border-default)' }}>
            {bindings?.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center" style={{ color: 'var(--text-muted)' }}>
                  No attributes defined. Use a template to auto-generate bindings.
                </td>
              </tr>
            ) : (
              bindings?.map((b: any) => (
                <tr key={b.binding_id || b.attribute_name}>
                  <td className="px-4 py-3">
                    <div style={{ color: 'var(--text-primary)' }}>{b.attribute_name}</div>
                    {b.validation_message && (
                      <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{b.validation_message}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs" style={{ color: b.signal_id ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                    {b.signal_id || "—"}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span title={b.validation_status || "unvalidated"}>
                      {statusIcon(b.validation_status)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {!b.signal_id ? (
                        <button
                          onClick={() => setBindingSignal({ attr: b.attribute_name, open: true })}
                          className="p-1.5 rounded hover:bg-gray-700"
                          title="Bind signal"
                        >
                          <Link2 className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
                        </button>
                      ) : (
                        <button
                          onClick={() => unbindMutation.mutate(b.binding_id)}
                          className="p-1.5 rounded hover:bg-gray-700"
                          title="Unbind signal"
                        >
                          <Unlink className="w-4 h-4" style={{ color: '#ef4444' }} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Bind Signal Dropdown */}
      {bindingSignal && (
        <div
          className="rounded-lg p-4 border"
          style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
              Bind signal to <code className="font-mono">{bindingSignal.attr}</code>
            </span>
            <button
              onClick={() => setBindingSignal(null)}
              className="text-xs px-2 py-1 rounded"
              style={{ color: 'var(--text-muted)' }}
            >
              Cancel
            </button>
          </div>
          <input
            type="text"
            placeholder="Search signals..."
            value={signalSearch}
            onChange={(e) => setSignalSearch(e.target.value)}
            className="w-full rounded px-3 py-2 text-sm border mb-2"
            style={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--border-default)', color: 'var(--text-primary)' }}
            autoFocus
          />
          <div className="max-h-48 overflow-y-auto space-y-1">
            {filteredSignals?.slice(0, 50).map((s: any) => (
              <button
                key={s.signal_id}
                onClick={() => bindMutation.mutate({ attr: bindingSignal.attr, signalId: s.signal_id })}
                className="w-full text-left px-3 py-2 rounded text-sm hover:bg-gray-700 flex items-center justify-between"
                style={{ color: 'var(--text-primary)' }}
              >
                <span className="font-mono text-xs">{s.signal_id}</span>
                <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{s.display_name || s.signal_name}</span>
              </button>
            ))}
            {filteredSignals?.length === 0 && (
              <div className="text-xs py-2 text-center" style={{ color: 'var(--text-muted)' }}>No signals found</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
