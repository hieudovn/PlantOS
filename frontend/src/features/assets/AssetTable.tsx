import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getAssets, deleteAsset } from "@/lib/api";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { StatusBadge } from "@/components/StatusBadge";
import { AssetFilters } from "./AssetFilters";
import { AssetTree } from "./AssetTree";
import { AssetForm } from "./AssetForm";
import { Search, Plus, Pencil, Trash2 } from "lucide-react";

export function AssetTable() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [viewMode, setViewMode] = useState<"tree" | "table">("tree");
  const [showForm, setShowForm] = useState(false);
  const [editAsset, setEditAsset] = useState<any | null>(null);
  const { plantId } = useWorkspace();

  const params: Record<string, string> = { plant_id: plantId };
  searchParams.forEach((v, k) => { params[k] = v; });

  const { data: assets, isLoading } = useQuery({
    queryKey: ["assets", plantId, params],
    queryFn: () => getAssets(params),
  });

  const filtered = assets?.filter((a: any) =>
    !search ||
    a.name.toLowerCase().includes(search.toLowerCase()) ||
    a.asset_id.toLowerCase().includes(search.toLowerCase())
  );

  async function handleDelete(assetId: string) {
    if (!confirm(`Delete asset "${assetId}"? This will soft-delete it.`)) return;
    try {
      await deleteAsset(assetId);
      queryClient.invalidateQueries({ queryKey: ["assets"] });
    } catch (err: any) {
      alert(err.message || "Delete failed");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Assets</h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{filtered?.length || 0} assets</span>
          <button
            onClick={() => { setEditAsset(null); setShowForm(true); }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium"
            style={{ backgroundColor: 'var(--accent-primary)', color: '#fff' }}
          >
            <Plus className="w-4 h-4" />
            Create Asset
          </button>
        </div>
      </div>

      <div className="flex gap-3 items-center">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search by name or ID..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-64 bg-gray-900 border border-gray-700 rounded pl-10 pr-3 py-2 text-sm"
          />
        </div>
        <AssetFilters />
      </div>

      <div className="flex items-center gap-2 mb-3">
        <button
          onClick={() => setViewMode("tree")}
          className={`px-3 py-1 text-xs rounded ${
            viewMode === "tree" ? "bg-gray-700 text-white" : "text-gray-500"
          }`}
        >
          🌳 Tree
        </button>
        <button
          onClick={() => setViewMode("table")}
          className={`px-3 py-1 text-xs rounded ${
            viewMode === "table" ? "bg-gray-700 text-white" : "text-gray-500"
          }`}
        >
          📋 Table
        </button>
      </div>

      {isLoading ? (
        <div className="text-gray-500">Loading...</div>
      ) : viewMode === "tree" ? (
        <AssetTree />
      ) : (
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400">
              <tr>
                <th className="text-left px-4 py-3">Asset ID</th>
                <th className="text-left px-4 py-3">Name</th>
                <th className="text-left px-4 py-3">Type</th>
                <th className="text-left px-4 py-3">Role</th>
                <th className="text-left px-4 py-3">Area</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-right px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {filtered?.map((a: any) => (
                <tr
                  key={a.asset_id}
                  className="hover:bg-gray-800/50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/assets/${a.asset_id}`)}
                >
                  <td className="px-4 py-3 font-mono text-xs">{a.asset_id}</td>
                  <td className="px-4 py-3">{a.name}</td>
                  <td className="px-4 py-3 text-gray-400">{a.asset_type}</td>
                  <td className="px-4 py-3">
                    <span className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--surface-hover)' }}>
                      {a.asset_role}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400">{a.area_id || "—"}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={a.lifecycle_status} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => { setEditAsset(a); setShowForm(true); }}
                        className="p-1 rounded hover:bg-gray-700"
                        title="Edit"
                      >
                        <Pencil className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
                      </button>
                      <button
                        onClick={() => handleDelete(a.asset_id)}
                        className="p-1 rounded hover:bg-gray-700"
                        title="Delete"
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

      {showForm && (
        <AssetForm
          mode={editAsset ? "edit" : "create"}
          asset={editAsset}
          onClose={() => { setShowForm(false); setEditAsset(null); }}
          onSaved={() => {}}
        />
      )}
    </div>
  );
}
