const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
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
