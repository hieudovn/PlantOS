// Use relative URLs — Vite proxy forwards /api to backend
const BASE = "";

export async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("plantos_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  const newToken = res.headers.get("X-New-Token");
  if (newToken) {
    localStorage.setItem("plantos_token", newToken);
  }

  if (res.status === 401 || res.status === 403) {
    localStorage.removeItem("plantos_token");
    if (token && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API ${res.status}`);
  }
  return res.json();
}

// ---- Plants ----
export const getPlants = () => fetchAPI<any[]>("/api/v1/plants");

// ---- Assets ----
export const getAssets = (params?: Record<string, string>) => {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return fetchAPI<any[]>(`/api/v1/assets${qs}`);
};
export const getAsset = (id: string) => fetchAPI<any>(`/api/v1/assets/${id}`);

// ---- Signals ----
export const getSignals = (params?: Record<string, string>) => {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return fetchAPI<any[]>(`/api/v1/signals${qs}`);
};

// ---- Measurements ----
export const getCurrentValues = (params: Record<string, string>) => {
  const qs = "?" + new URLSearchParams(params).toString();
  return fetchAPI<any[]>(`/api/v1/measurements/current${qs}`);
};

export const getHistory = (params: Record<string, string>) => {
  const qs = "?" + new URLSearchParams(params).toString();
  return fetchAPI<any>(`/api/v1/measurements/history${qs}`);
};

// ---- Edge Nodes ----
export interface EdgeNode {
  edge_node_id: string;
  node_type: string;
  status: string;
  last_heartbeat: string | null;
  hostname: string | null;
  ip_address: string | null;
  edge_version: string | null;
  signal_count: number;
  backlog_count: number;
  center_sync?: string;
  disk_usage_mb?: number;
  workspace_id?: string;
}

export const getEdgeNodes = () => fetchAPI<EdgeNode[]>("/api/v1/edge-nodes");
export const getEdgeNode = (id: string) => fetchAPI<any>(`/api/v1/edge-nodes/${id}`);
export const getEdgeConnectors = (id: string) => fetchAPI<any[]>(`/api/v1/edge-nodes/${id}/connectors`);
export const getEdgeHeartbeats = (id: string, limit = 100) => fetchAPI<any[]>(`/api/v1/edge-nodes/${id}/heartbeats?limit=${limit}`);
export const getEdgeCommands = (id: string) => fetchAPI<any[]>(`/api/v1/edge-nodes/${id}/commands`);
export const createEdgeCommand = (id: string, commandType: string, target?: string) =>
  fetchAPI<any>(`/api/v1/edge-nodes/${id}/commands`, {
    method: "POST",
    body: JSON.stringify({ command_type: commandType, target }),
  });

// ---- System Metrics ----
export const getSystemMetrics = () => fetchAPI<any>("/api/v1/system/metrics");

// ---- Stub exports for features not yet migrated to fetchAPI ----
export async function getAlarms(params?: any): Promise<any[]> { const p = params ? "?" + new URLSearchParams(params).toString() : ""; return fetchAPI("/api/v1/alarms" + p); }
export async function getBindings(assetId: string): Promise<any[]> { return fetchAPI(`/api/v1/assets/${assetId}/bindings`); }
export async function createBinding(data: any): Promise<any> { return fetchAPI("/api/v1/bindings", { method: "POST", body: JSON.stringify(data) }); }
export async function deleteBinding(id: string): Promise<void> { await fetchAPI(`/api/v1/bindings/${id}`, { method: "DELETE" }); }
export async function validateBindings(data: any): Promise<any> { return fetchAPI("/api/v1/bindings/validate", { method: "POST", body: JSON.stringify(data) }); }
export async function deleteAsset(id: string): Promise<void> { await fetchAPI(`/api/v1/assets/${id}`, { method: "DELETE" }); }
export async function getVocabulary(): Promise<any> { return fetchAPI("/api/v1/vocabulary"); }
export async function getAreas(params?: Record<string, string>): Promise<any[]> {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return fetchAPI(`/api/v1/areas${qs}`);
}
export async function getTemplates(): Promise<any[]> { return fetchAPI("/api/v1/asset-templates"); }
export async function createAsset(data: any): Promise<any> { return fetchAPI("/api/v1/assets", { method: "POST", body: JSON.stringify(data) }); }
export async function updateAsset(id: string, data: any): Promise<any> { return fetchAPI(`/api/v1/assets/${id}`, { method: "PUT", body: JSON.stringify(data) }); }
export async function bindFromTemplate(assetId: string, templateId: string): Promise<any> { return fetchAPI(`/api/v1/assets/${assetId}/bind`, { method: "POST", body: JSON.stringify({ template_id: templateId }) }); }
export async function getCalcSignals(): Promise<any[]> { return fetchAPI("/api/v1/calculated-signals"); }
export async function createCalcSignal(data: any): Promise<any> { return fetchAPI("/api/v1/calculated-signals", { method: "POST", body: JSON.stringify(data) }); }
export async function updateCalcSignal(id: string, data: any): Promise<any> { return fetchAPI(`/api/v1/calculated-signals/${id}`, { method: "PUT", body: JSON.stringify(data) }); }
export async function deleteCalcSignal(id: string): Promise<void> { await fetchAPI(`/api/v1/calculated-signals/${id}`, { method: "DELETE" }); }
export async function testCalcSignal(data: any): Promise<any> { return fetchAPI("/api/v1/calculated-signals/test", { method: "POST", body: JSON.stringify(data) }); }
export async function executeCalcSignal(id: string): Promise<any> { return fetchAPI(`/api/v1/calculated-signals/${id}/execute`, { method: "POST" }); }
export async function validateFormula(data: any): Promise<any> { return fetchAPI("/api/v1/formulas/validate", { method: "POST", body: JSON.stringify(data) }); }
export async function getKpis(params?: Record<string, string>): Promise<any[]> {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return fetchAPI(`/api/v1/kpis${qs}`);
}
export async function createKpi(data: any): Promise<any> { return fetchAPI("/api/v1/kpis", { method: "POST", body: JSON.stringify(data) }); }
export async function updateKpi(id: string, data: any): Promise<any> { return fetchAPI(`/api/v1/kpis/${id}`, { method: "PUT", body: JSON.stringify(data) }); }
export async function deleteKpi(id: string): Promise<void> { await fetchAPI(`/api/v1/kpis/${id}`, { method: "DELETE" }); }
export async function testKpi(data: any): Promise<any> { return fetchAPI("/api/v1/kpis/test", { method: "POST", body: JSON.stringify(data) }); }
