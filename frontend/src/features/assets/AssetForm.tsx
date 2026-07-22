import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getVocabulary, getAreas, getAssets, getTemplates, createAsset, updateAsset, bindFromTemplate, fetchAPI } from "@/lib/api";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { X, Loader2 } from "lucide-react";

interface AssetFormProps {
  mode: "create" | "edit";
  asset?: any;
  onClose: () => void;
  onSaved: () => void;
}

export function AssetForm({ mode, asset, onClose, onSaved }: AssetFormProps) {
  const queryClient = useQueryClient();
  const { plantId } = useWorkspace();

  const { data: vocab } = useQuery({ queryKey: ["vocabulary"], queryFn: getVocabulary });
  const { data: areas } = useQuery({ queryKey: ["areas", plantId], queryFn: () => getAreas() });
  const { data: allAssets } = useQuery({ queryKey: ["assets-all"], queryFn: () => getAssets() });
  const { data: templates } = useQuery({ queryKey: ["templates"], queryFn: getTemplates });

  const [form, setForm] = useState({
    asset_id: "",
    asset_code: "",
    name: "",
    asset_type: "",
    asset_role: "equipment",
    area_id: "",
    parent_asset_id: "",
    criticality: "medium",
    lifecycle_status: "active",
    manufacturer: "",
    model: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState("");

  useEffect(() => {
    if (mode === "edit" && asset) {
      setForm({
        asset_id: asset.asset_id || "",
        asset_code: asset.asset_code || "",
        name: asset.name || "",
        asset_type: asset.asset_type || "",
        asset_role: asset.asset_role || "equipment",
        area_id: asset.area_id || "",
        parent_asset_id: asset.parent_asset_id || "",
        criticality: asset.criticality || "medium",
        lifecycle_status: asset.lifecycle_status || "active",
        manufacturer: asset.manufacturer || "",
        model: asset.model || "",
      });
    }
  }, [mode, asset]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload: any = { ...form };
      // Remove empty strings for optional fields
      if (!payload.asset_code) delete payload.asset_code;
      if (!payload.area_id) delete payload.area_id;
      if (!payload.parent_asset_id) delete payload.parent_asset_id;
      if (!payload.manufacturer) delete payload.manufacturer;
      if (!payload.model) delete payload.model;
      payload.plant_id = plantId;

      if (mode === "create") {
        return createAsset(payload);
      } else {
        // Only send changed fields for update
        const changed: any = {};
        for (const key of Object.keys(form)) {
          const orig = (asset as any)?.[key] ?? "";
          const current = (form as any)[key] ?? "";
          if (String(current) !== String(orig)) {
            changed[key] = current;
          }
        }
        if (Object.keys(changed).length === 0) return;
        return updateAsset(asset!.asset_id, changed);
      }
    },
    onSuccess: async (result) => {
      // If a template was selected, auto-generate bindings
      if (selectedTemplate && mode === "create" && result?.asset_id) {
        try {
          await bindFromTemplate(result.asset_id, selectedTemplate);
        } catch (_) {
          // Non-critical — template bindings are optional
        }
      }
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      onSaved();
      onClose();
    },
    onError: (err: any) => {
      setError(err.message || "Save failed");
    },
  });

  const handleChange = (field: string, value: string) => {
    if (field === "asset_id" && mode === "create") {
      // Replace spaces with underscores
      value = value.replace(/\s+/g, "_");
    }
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const isValid = form.asset_id.trim() && form.name.trim() && form.asset_type.trim();

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: "rgba(0,0,0,0.6)" }}
      onClick={onClose}
    >
      <div
        className="rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6"
        style={{ backgroundColor: "var(--surface-card)", borderColor: "var(--border-default)", border: "1px solid" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
            {mode === "create" ? "Create Asset" : "Edit Asset"}
          </h2>
          <button onClick={onClose} className="p-1 rounded hover:bg-gray-700" style={{ color: "var(--text-secondary)" }}>
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 rounded text-sm" style={{ backgroundColor: "rgba(239,68,68,0.15)", color: "#ef4444", border: "1px solid rgba(239,68,68,0.3)" }}>
            {error}
          </div>
        )}

        {/* Form */}
        <div className="grid grid-cols-2 gap-4">
          {/* asset_id */}
          <div className="col-span-1">
            <label className="block text-xs mb-1" style={{ color: "var(--text-secondary)" }}>
              Asset ID <span style={{ color: "#ef4444" }}>*</span>
            </label>
            <input
              type="text"
              value={form.asset_id}
              onChange={(e) => handleChange("asset_id", e.target.value)}
              readOnly={mode === "edit"}
              maxLength={128}
              placeholder="e.g. PUMP-201"
              className="w-full rounded px-3 py-2 text-sm border"
              style={{
                backgroundColor: "var(--surface-primary)",
                borderColor: "var(--border-default)",
                color: "var(--text-primary)",
                opacity: mode === "edit" ? 0.6 : 1,
              }}
            />
          </div>

          {/* asset_code */}
          <div className="col-span-1">
            <label className="block text-xs mb-1" style={{ color: "var(--text-secondary)" }}>
              Asset Code
            </label>
            <input
              type="text"
              value={form.asset_code}
              onChange={(e) => handleChange("asset_code", e.target.value)}
              placeholder="e.g. P201"
              className="w-full rounded px-3 py-2 text-sm border"
              style={{ backgroundColor: "var(--surface-primary)", borderColor: "var(--border-default)", color: "var(--text-primary)" }}
            />
          </div>

          {/* name */}
          <div className="col-span-2">
            <label className="block text-xs mb-1" style={{ color: "var(--text-secondary)" }}>
              Name <span style={{ color: "#ef4444" }}>*</span>
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => handleChange("name", e.target.value)}
              placeholder="e.g. Booster Pump 201"
              className="w-full rounded px-3 py-2 text-sm border"
              style={{ backgroundColor: "var(--surface-primary)", borderColor: "var(--border-default)", color: "var(--text-primary)" }}
            />
          </div>

          {/* asset_type */}
          <div className="col-span-1">
            <label className="block text-xs mb-1" style={{ color: "var(--text-secondary)" }}>
              Type <span style={{ color: "#ef4444" }}>*</span>
            </label>
            <select
              value={form.asset_type}
              onChange={(e) => handleChange("asset_type", e.target.value)}
              className="w-full rounded px-3 py-2 text-sm border"
              style={{ backgroundColor: "var(--surface-primary)", borderColor: "var(--border-default)", color: "var(--text-primary)" }}
            >
              <option value="">Select type...</option>
              {(vocab?.asset_types || []).map((t: string) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          {/* asset_role */}
          <div className="col-span-1">
            <label className="block text-xs mb-1" style={{ color: "var(--text-secondary)" }}>
              Role <span style={{ color: "#ef4444" }}>*</span>
            </label>
            <select
              value={form.asset_role}
              onChange={(e) => handleChange("asset_role", e.target.value)}
              className="w-full rounded px-3 py-2 text-sm border"
              style={{ backgroundColor: "var(--surface-primary)", borderColor: "var(--border-default)", color: "var(--text-primary)" }}
            >
              {(vocab?.asset_roles || []).map((r: string) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          {/* template selector — shown only in create mode */}
          {mode === "create" && form.asset_type && (
            <div className="col-span-2">
              <label className="block text-xs mb-1" style={{ color: "var(--text-secondary)" }}>
                Template (optional)
              </label>
              <select
                value={selectedTemplate}
                onChange={(e) => setSelectedTemplate(e.target.value)}
                className="w-full rounded px-3 py-2 text-sm border"
                style={{ backgroundColor: "var(--surface-primary)", borderColor: "var(--border-default)", color: "var(--text-primary)" }}
              >
                <option value="">Custom (no template)</option>
                {(templates || [])
                  .filter((t: any) => t.asset_type === form.asset_type)
                  .map((t: any) => (
                    <option key={t.template_id} value={t.template_id}>{t.name}</option>
                  ))}
              </select>
              {selectedTemplate && (
                <div className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                  Attributes will be auto-generated from template after creation.
                </div>
              )}
            </div>
          )}

          {/* area_id */}
          <div className="col-span-1">
            <label className="block text-xs mb-1" style={{ color: "var(--text-secondary)" }}>
              Area
            </label>
            <select
              value={form.area_id}
              onChange={(e) => handleChange("area_id", e.target.value)}
              className="w-full rounded px-3 py-2 text-sm border"
              style={{ backgroundColor: "var(--surface-primary)", borderColor: "var(--border-default)", color: "var(--text-primary)" }}
            >
              <option value="">No area</option>
              {(areas || []).map((a: any) => (
                <option key={a.area_id} value={a.area_id}>{a.name} ({a.area_id})</option>
              ))}
            </select>
          </div>

          {/* parent_asset_id */}
          <div className="col-span-1">
            <label className="block text-xs mb-1" style={{ color: "var(--text-secondary)" }}>
              Parent Asset
            </label>
            <select
              value={form.parent_asset_id}
              onChange={(e) => handleChange("parent_asset_id", e.target.value)}
              className="w-full rounded px-3 py-2 text-sm border"
              style={{ backgroundColor: "var(--surface-primary)", borderColor: "var(--border-default)", color: "var(--text-primary)" }}
            >
              <option value="">No parent</option>
              {(allAssets || [])
                .filter((a: any) => a.asset_id !== form.asset_id)
                .map((a: any) => (
                  <option key={a.asset_id} value={a.asset_id}>{a.name} ({a.asset_id})</option>
                ))}
            </select>
          </div>

          {/* criticality */}
          <div className="col-span-1">
            <label className="block text-xs mb-1" style={{ color: "var(--text-secondary)" }}>
              Criticality
            </label>
            <select
              value={form.criticality}
              onChange={(e) => handleChange("criticality", e.target.value)}
              className="w-full rounded px-3 py-2 text-sm border"
              style={{ backgroundColor: "var(--surface-primary)", borderColor: "var(--border-default)", color: "var(--text-primary)" }}
            >
              {(vocab?.criticality_levels || []).map((c: string) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* lifecycle_status */}
          <div className="col-span-1">
            <label className="block text-xs mb-1" style={{ color: "var(--text-secondary)" }}>
              Lifecycle Status
            </label>
            <select
              value={form.lifecycle_status}
              onChange={(e) => handleChange("lifecycle_status", e.target.value)}
              className="w-full rounded px-3 py-2 text-sm border"
              style={{ backgroundColor: "var(--surface-primary)", borderColor: "var(--border-default)", color: "var(--text-primary)" }}
            >
              {(vocab?.lifecycle_statuses || []).map((s: string) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* manufacturer */}
          <div className="col-span-1">
            <label className="block text-xs mb-1" style={{ color: "var(--text-secondary)" }}>
              Manufacturer
            </label>
            <input
              type="text"
              value={form.manufacturer}
              onChange={(e) => handleChange("manufacturer", e.target.value)}
              placeholder="e.g. Grundfos"
              className="w-full rounded px-3 py-2 text-sm border"
              style={{ backgroundColor: "var(--surface-primary)", borderColor: "var(--border-default)", color: "var(--text-primary)" }}
            />
          </div>

          {/* model */}
          <div className="col-span-1">
            <label className="block text-xs mb-1" style={{ color: "var(--text-secondary)" }}>
              Model
            </label>
            <input
              type="text"
              value={form.model}
              onChange={(e) => handleChange("model", e.target.value)}
              placeholder="e.g. CR-45-3"
              className="w-full rounded px-3 py-2 text-sm border"
              style={{ backgroundColor: "var(--surface-primary)", borderColor: "var(--border-default)", color: "var(--text-primary)" }}
            />
          </div>
        </div>

        {/* Buttons */}
        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded text-sm"
            style={{ backgroundColor: "var(--surface-hover)", color: "var(--text-secondary)" }}
          >
            Cancel
          </button>
          <button
            onClick={() => saveMutation.mutate()}
            disabled={!isValid || saveMutation.isPending}
            className="px-4 py-2 rounded text-sm font-medium flex items-center gap-2"
            style={{
              backgroundColor: isValid ? "var(--accent-primary)" : "var(--surface-hover)",
              color: isValid ? "#fff" : "var(--text-muted)",
              opacity: saveMutation.isPending ? 0.7 : 1,
            }}
          >
            {saveMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
            {mode === "create" ? "Create" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
