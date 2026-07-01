// Use relative URLs — Vite proxy forwards /api to backend
const BASE = "";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("plantos_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  // Sliding expiration: update token if server returned a new one
  const newToken = res.headers.get("X-New-Token");
  if (newToken) {
    localStorage.setItem("plantos_token", newToken);
  }

  if (res.status === 401) {
    localStorage.removeItem("plantos_token");
    // Avoid redirect loop: only redirect if not already on login page
    if (!window.location.pathname.startsWith("/login")) {
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

// ---- System Metrics ----
export const getSystemMetrics = () => fetchAPI<any>("/api/v1/system/metrics");
