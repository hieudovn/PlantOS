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
  } else {
    const DEMO_API_KEY = import.meta.env.VITE_API_KEY || "";
    if (DEMO_API_KEY) {
      headers["X-API-Key"] = DEMO_API_KEY;
    }
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  const newToken = res.headers.get("X-New-Token");
  if (newToken) {
    localStorage.setItem("plantos_token", newToken);
  }

  if (res.status === 401) {
    localStorage.removeItem("plantos_token");
    if (token && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API ${res.status}`);
  }
  return res.json();
}

/** Like fetchAPI but returns the raw Response (for 204 etc.). */
export async function fetchAPIRaw(path: string, options?: RequestInit): Promise<Response> {
  const token = localStorage.getItem("plantos_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  } else {
    const DEMO_API_KEY = import.meta.env.VITE_API_KEY || "";
    if (DEMO_API_KEY) {
      headers["X-API-Key"] = DEMO_API_KEY;
    }
  }
  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    localStorage.removeItem("plantos_token");
    if (token && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
  }
  if (!res.ok && res.status !== 204) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API ${res.status}`);
  }
  return res;
}

// ---- Edge Fleet ----
export const getEdgeNodes = () => fetchAPI<any[]>("/api/v1/edge-nodes");

// ---- Plants ----
export const getPlants = () => fetchAPI<any[]>("/api/v1/plants");

// ---- Assets ----
export const getAssets = (params?: Record<string, string>) => {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return fetchAPI<any[]>(`/api/v1/assets${qs}`);
};
export const getAsset = (id: string) => fetchAPI<any>(`/api/v1/assets/${id}`);
export const getVocabulary = () => fetchAPI<any>("/api/v1/assets/vocabulary");
export const createAsset = (data: any) =>
  fetchAPI<any>("/api/v1/assets", { method: "POST", body: JSON.stringify(data) });
export const updateAsset = (id: string, data: any) =>
  fetchAPI<any>(`/api/v1/assets/${id}`, { method: "PATCH", body: JSON.stringify(data) });
export const deleteAsset = (id: string) =>
  fetchAPIRaw(`/api/v1/assets/${id}`, { method: "DELETE" });

// ---- Areas ----
export const getAreas = (params?: Record<string, string>) => {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return fetchAPI<any[]>(`/api/v1/areas${qs}`);
};

// ---- Asset Templates ----
export const getTemplates = () => fetchAPI<any[]>("/api/v1/asset-templates");
export const seedTemplates = () => fetchAPI<any>("/api/v1/asset-templates/seed", { method: "POST" });

// ---- Asset Bindings ----
export const getBindings = (assetId: string) => fetchAPI<any[]>(`/api/v1/assets/${assetId}/bindings`);
export const createBinding = (assetId: string, data: any) =>
  fetchAPI<any>(`/api/v1/assets/${assetId}/bindings`, { method: "POST", body: JSON.stringify(data) });
export const deleteBinding = (assetId: string, bindingId: string) =>
  fetchAPIRaw(`/api/v1/assets/${assetId}/bindings/${bindingId}`, { method: "DELETE" });
export const validateBindings = (assetId: string) =>
  fetchAPI<any>(`/api/v1/assets/${assetId}/bindings/validate`, { method: "POST" });
export const bindFromTemplate = (assetId: string, templateId: string) =>
  fetchAPI<any[]>(`/api/v1/assets/${assetId}/bindings/from-template/${templateId}`, { method: "POST" });

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

// ---- Alarms ----
export const getAlarms = (params?: Record<string, string>) => {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return fetchAPI<any[]>(`/api/v1/alarms${qs}`);
};

// ---- System ----
export const getSystemMetrics = () => fetchAPI<any>("/api/v1/system/metrics");
