import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { validateFormula, getSignals, getCalcSignals } from "@/lib/api";
import { Loader2, CheckCircle, XCircle } from "lucide-react";

interface FormulaEditorProps {
  mode: "create" | "edit";
  initial?: any;
  onSave: (data: any) => void;
  onCancel: () => void;
  scope?: { type: string; id: string }; // for KPI scope
}

export function FormulaEditor({ mode, initial, onSave, onCancel, scope }: FormulaEditorProps) {
  const [formula, setFormula] = useState(initial?.formula || "");
  const [name, setName] = useState(initial?.name || "");
  const [displayName, setDisplayName] = useState(initial?.display_name || "");
  const [inputs, setInputs] = useState<{ variable: string; signal_id: string }[]>(
    initial?.inputs?.map((i: any) => ({ variable: i.variable_name, signal_id: i.signal_id })) || []
  );
  const [outputSignalId, setOutputSignalId] = useState(initial?.output_signal_id || "");
  const [outputUnit, setOutputUnit] = useState(initial?.output_unit || "");
  const [validationResult, setValidationResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchVars, setSearchVars] = useState<Record<number, string>>({});

  const { data: allSignals } = useQuery({ queryKey: ["signals-all"], queryFn: () => getSignals() });

  const validateMutation = useMutation({
    mutationFn: () =>
      validateFormula({
        formula,
        input_names: inputs.map((i) => i.variable),
      }),
    onSuccess: setValidationResult,
    onError: (err: any) => setValidationResult({ valid: false, errors: [err.message] }),
  });

  const nextVar = () => {
    const used = new Set(inputs.map((i) => i.variable));
    for (let i = 0; i < 26; i++) {
      const letter = String.fromCharCode(65 + i);
      if (!used.has(letter)) return letter;
    }
    return `V${inputs.length + 1}`;
  };

  const addInput = () => {
    setInputs([...inputs, { variable: nextVar(), signal_id: "" }]);
  };

  const removeInput = (idx: number) => {
    setInputs(inputs.filter((_, i) => i !== idx));
  };

  const updateInput = (idx: number, field: string, value: string) => {
    const updated = [...inputs];
    updated[idx] = { ...updated[idx], [field]: value };
    setInputs(updated);
  };

  const filteredSignals = (idx: number) => {
    const search = (searchVars[idx] || "").toLowerCase();
    if (!search) return (allSignals || []).slice(0, 20);
    return (allSignals || []).filter(
      (s: any) =>
        s.signal_id.toLowerCase().includes(search) ||
        s.display_name?.toLowerCase().includes(search)
    ).slice(0, 50);
  };

  const handleSave = () => {
    if (!name.trim() || !formula.trim()) {
      setError("Name and formula are required");
      return;
    }
    onSave({
      ...(initial || {}),
      name,
      display_name: displayName || undefined,
      formula,
      inputs: inputs.map((i) => ({ variable_name: i.variable, signal_id: i.signal_id })),
      output_signal_id: outputSignalId || undefined,
      output_unit: outputUnit || undefined,
    });
  };

  const id = initial?.calc_signal_id || initial?.kpi_id || name.toLowerCase().replace(/[^a-z0-9_]/g, "_");

  return (
    <div className="space-y-6" style={{ color: 'var(--text-primary)' }}>
      {/* Name & ID */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>Name *</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="My Formula"
            className="w-full rounded px-3 py-2 text-sm border"
            style={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--border-default)', color: 'var(--text-primary)' }}
          />
        </div>
        <div>
          <label className="block text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>Display Name</label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="My Formula Display"
            className="w-full rounded px-3 py-2 text-sm border"
            style={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--border-default)', color: 'var(--text-primary)' }}
          />
        </div>
      </div>

      {/* Inputs */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Inputs</label>
          <button onClick={addInput} className="text-xs px-2 py-1 rounded" style={{ backgroundColor: 'var(--surface-hover)', color: 'var(--accent-primary)' }}>
            + Add Input
          </button>
        </div>
        {inputs.length === 0 && (
          <div className="text-xs py-2" style={{ color: 'var(--text-muted)' }}>No inputs defined. Add signal inputs to use in your formula.</div>
        )}
        {inputs.map((inp, idx) => (
          <div key={idx} className="flex items-center gap-2 mb-2">
            <span className="text-sm font-mono w-8" style={{ color: 'var(--accent-primary)' }}>{inp.variable}</span>
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>=</span>
            <div className="flex-1 relative">
              <input
                type="text"
                placeholder="Search signal..."
                value={searchVars[idx] || ""}
                onChange={(e) => setSearchVars({ ...searchVars, [idx]: e.target.value })}
                className="w-full rounded px-3 py-2 text-sm border"
                style={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--border-default)', color: 'var(--text-primary)' }}
              />
              {searchVars[idx] !== undefined && (
                <div className="absolute z-10 mt-1 w-full rounded border max-h-40 overflow-y-auto" style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }}>
                  {filteredSignals(idx).map((s: any) => (
                    <button
                      key={s.signal_id}
                      onClick={() => { updateInput(idx, "signal_id", s.signal_id); setSearchVars({ ...searchVars, [idx]: "" }); }}
                      className="w-full text-left px-3 py-1.5 text-xs hover:bg-gray-700"
                      style={{ color: inp.signal_id === s.signal_id ? 'var(--accent-primary)' : 'var(--text-primary)' }}
                    >
                      {s.signal_id}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {inp.signal_id && (
              <span className="text-xs truncate max-w-[200px]" style={{ color: 'var(--text-muted)' }}>{inp.signal_id}</span>
            )}
            <button onClick={() => removeInput(idx)} className="text-xs px-1.5 py-0.5 rounded" style={{ color: '#ef4444' }}>✕</button>
          </div>
        ))}
      </div>

      {/* Formula */}
      <div>
        <label className="block text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>Formula *</label>
        <textarea
          value={formula}
          onChange={(e) => setFormula(e.target.value)}
          rows={4}
          placeholder="e.g. A * 0.5 + normalize(B, 0, 100)"
          className="w-full rounded px-3 py-2 text-sm font-mono border"
          style={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--border-default)', color: 'var(--text-primary)' }}
        />
        <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
          Use variable names (A, B, C...) defined above. Functions: abs, round, min, max, clamp, normalize.
        </div>
      </div>

      {/* Validate */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => validateMutation.mutate()}
          disabled={!formula.trim() || validateMutation.isPending}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm"
          style={{ backgroundColor: 'var(--surface-hover)', color: 'var(--text-secondary)' }}
        >
          {validateMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
          Test Formula
        </button>
        {validationResult && (
          <div className="flex items-center gap-2 text-sm">
            {validationResult.valid ? (
              <CheckCircle className="w-4 h-4" style={{ color: '#22c55e' }} />
            ) : (
              <XCircle className="w-4 h-4" style={{ color: '#ef4444' }} />
            )}
            <span style={{ color: validationResult.valid ? '#22c55e' : '#ef4444' }}>
              {validationResult.valid ? "Valid" : validationResult.errors?.[0] || "Invalid"}
            </span>
            {validationResult.preview_value !== null && validationResult.preview_value !== undefined && (
              <span className="ml-2" style={{ color: 'var(--text-muted)' }}>
                Preview: {validationResult.preview_value.toFixed(2)}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Output Signal (for calc signals only) */}
      {!scope && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>Output Signal ID</label>
            <input
              type="text"
              value={outputSignalId}
              onChange={(e) => setOutputSignalId(e.target.value)}
              placeholder="e.g. PUMP-101.combined_index"
              className="w-full rounded px-3 py-2 text-sm border"
              style={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--border-default)', color: 'var(--text-primary)' }}
            />
          </div>
          <div>
            <label className="block text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>Output Unit</label>
            <input
              type="text"
              value={outputUnit}
              onChange={(e) => setOutputUnit(e.target.value)}
              placeholder="e.g. m3/h"
              className="w-full rounded px-3 py-2 text-sm border"
              style={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--border-default)', color: 'var(--text-primary)' }}
            />
          </div>
        </div>
      )}

      {error && (
        <div className="text-sm" style={{ color: '#ef4444' }}>{error}</div>
      )}

      {/* Buttons */}
      <div className="flex justify-end gap-3 pt-2">
        <button
          onClick={onCancel}
          className="px-4 py-2 rounded text-sm"
          style={{ backgroundColor: 'var(--surface-hover)', color: 'var(--text-secondary)' }}
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={!name.trim() || !formula.trim()}
          className="px-4 py-2 rounded text-sm font-medium"
          style={{
            backgroundColor: name.trim() && formula.trim() ? 'var(--accent-primary)' : 'var(--surface-hover)',
            color: name.trim() && formula.trim() ? '#fff' : 'var(--text-muted)',
          }}
        >
          {mode === "create" ? "Create" : "Save"}
        </button>
      </div>
    </div>
  );
}
