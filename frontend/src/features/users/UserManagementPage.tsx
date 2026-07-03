import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";
import { Plus, Edit3, Lock, Trash2, X, Shield } from "lucide-react";

interface User {
  id: string;
  username: string;
  display_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const ROLE_BADGE: Record<string, { color: string; label: string }> = {
  admin: { color: "var(--status-critical)", label: "Admin" },
  engineer: { color: "var(--status-warning)", label: "Engineer" },
  operator: { color: "var(--status-normal)", label: "Operator" },
};

function UserModal({ user, onClose }: { user?: User | null; onClose: () => void }) {
  const queryClient = useQueryClient();
  const isEdit = !!user;
  const [username, setUsername] = useState(user?.username || "");
  const [displayName, setDisplayName] = useState(user?.display_name || "");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState(user?.role || "operator");
  const [error, setError] = useState("");

  const saveMutation = useMutation({
    mutationFn: (body: any) => {
      if (isEdit) {
        return fetchAPI(`/api/v1/users/${user!.id}`, { method: "PUT", body: JSON.stringify(body) });
      }
      return fetchAPI("/api/v1/users", { method: "POST", body: JSON.stringify(body) });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      onClose();
    },
    onError: (err: any) => setError(err.message || "Failed to save"),
  });

  const handleSave = () => {
    if (!isEdit && !username.trim()) { setError("Username is required"); return; }
    if (!isEdit && !password) { setError("Password is required"); return; }
    const body: any = { display_name: displayName, role };
    if (!isEdit) { body.username = username; body.password = password; }
    if (password) body.password = password;
    saveMutation.mutate(body);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ backgroundColor: 'rgba(0,0,0,0.6)' }}>
      <div style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }} className="rounded-lg border w-96 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
            {isEdit ? "Edit User" : "New User"}
          </h3>
          <button onClick={onClose} style={{ color: 'var(--text-muted)' }}><X className="w-5 h-5" /></button>
        </div>

        {error && <div className="text-xs mb-3 p-2 rounded" style={{ color: 'var(--status-critical)', backgroundColor: 'rgba(239,68,68,0.1)' }}>{error}</div>}

        <div className="space-y-3">
          {!isEdit && (
            <div>
              <label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Username</label>
              <input value={username} onChange={e => setUsername(e.target.value)}
                className="w-full mt-1 px-3 py-2 rounded text-sm border" style={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--border-default)', color: 'var(--text-primary)' }} />
            </div>
          )}
          <div>
            <label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Display Name</label>
            <input value={displayName} onChange={e => setDisplayName(e.target.value)}
              className="w-full mt-1 px-3 py-2 rounded text-sm border" style={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--border-default)', color: 'var(--text-primary)' }} />
          </div>
          <div>
            <label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Password {isEdit && "(leave blank to keep)"}</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              className="w-full mt-1 px-3 py-2 rounded text-sm border" style={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--border-default)', color: 'var(--text-primary)' }} />
          </div>
          <div>
            <label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Role</label>
            <select value={role} onChange={e => setRole(e.target.value)}
              className="w-full mt-1 px-3 py-2 rounded text-sm border" style={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--border-default)', color: 'var(--text-primary)' }}>
              <option value="operator">Operator</option>
              <option value="engineer">Engineer</option>
              <option value="admin">Admin</option>
            </select>
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <button onClick={onClose} className="px-4 py-2 rounded text-sm" style={{ color: 'var(--text-secondary)' }}>Cancel</button>
          <button onClick={handleSave} disabled={saveMutation.isPending}
            className="px-4 py-2 rounded text-sm text-white font-medium" style={{ backgroundColor: 'var(--accent-primary)' }}>
            {saveMutation.isPending ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}

export function UserManagementPage() {
  const queryClient = useQueryClient();
  const [modalUser, setModalUser] = useState<User | null | undefined>(undefined);
  const [filterRole, setFilterRole] = useState("all");

  const { data: users, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: () => fetchAPI<User[]>("/api/v1/users"),
    refetchInterval: 30000,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => fetchAPI(`/api/v1/users/${id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });

  const filtered = (users || []).filter(u => filterRole === "all" || u.role === filterRole);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>User Management</h1>
        <button onClick={() => setModalUser(null)}
          className="flex items-center gap-2 px-4 py-2 rounded text-sm font-medium text-white"
          style={{ backgroundColor: 'var(--accent-primary)' }}>
          <Plus className="w-4 h-4" /> Add User
        </button>
      </div>

      <div className="flex gap-3">
        <select value={filterRole} onChange={e => setFilterRole(e.target.value)}
          className="px-3 py-1.5 rounded text-sm border" style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)', color: 'var(--text-primary)' }}>
          <option value="all">All Roles</option>
          <option value="admin">Admin</option>
          <option value="engineer">Engineer</option>
          <option value="operator">Operator</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-sm" style={{ color: 'var(--text-muted)' }}>Loading...</div>
      ) : (
        <div style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }} className="rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead style={{ borderColor: 'var(--border-default)' }} className="border-b">
              <tr style={{ color: 'var(--text-secondary)' }}>
                <th className="text-left px-4 py-3 font-medium">Username</th>
                <th className="text-left px-4 py-3 font-medium">Display Name</th>
                <th className="text-left px-4 py-3 font-medium">Role</th>
                <th className="text-left px-4 py-3 font-medium">Status</th>
                <th className="text-right px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(u => (
                <tr key={u.id} style={{ borderColor: 'var(--border-subtle)' }} className="border-b last:border-b-0">
                  <td className="px-4 py-3 font-medium" style={{ color: 'var(--text-primary)' }}>{u.username}</td>
                  <td className="px-4 py-3" style={{ color: 'var(--text-secondary)' }}>{u.display_name}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium"
                      style={{ color: ROLE_BADGE[u.role]?.color, backgroundColor: ROLE_BADGE[u.role]?.color + '20' }}>
                      <Shield className="w-3 h-3" /> {ROLE_BADGE[u.role]?.label || u.role}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs" style={{ color: u.is_active ? 'var(--status-normal)' : 'var(--status-offline)' }}>
                      {u.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => setModalUser(u)} className="p-1.5 rounded hover:brightness-110" title="Edit"
                        style={{ color: 'var(--text-muted)' }}><Edit3 className="w-4 h-4" /></button>
                      <button onClick={() => { if (confirm(`Deactivate ${u.username}?`)) deleteMutation.mutate(u.id); }}
                        className="p-1.5 rounded hover:brightness-110" title="Deactivate"
                        style={{ color: 'var(--status-critical)' }}><Trash2 className="w-4 h-4" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modalUser !== undefined && <UserModal user={modalUser} onClose={() => setModalUser(undefined)} />}
    </div>
  );
}
