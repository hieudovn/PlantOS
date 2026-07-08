// PlantOS Edge v2 — API client with auth headers and CSRF protection

const API = {

  /** Get CSRF token from cookie set by auth middleware */
  _getCsrfToken() {
    return document.cookie
      .split("; ")
      .find(row => row.startsWith("plantos_csrf="))
      ?.split("=")[1] || "";
  },

  /** Generic fetch wrapper */
  async _fetch(path, options = {}) {
    const headers = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    // Add CSRF token for state-changing methods
    if (options.method && !["GET", "HEAD"].includes(options.method)) {
      headers["X-CSRF-Token"] = this._getCsrfToken();
    }

    const res = await fetch(path, {
      ...options,
      headers,
      credentials: "same-origin",
    });

    if (res.status === 401) {
      // Session expired — redirect to login
      window.location.href = "/login.html";
      throw new Error("Session expired");
    }

    if (res.status === 403) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Forbidden");
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `HTTP ${res.status}`);
    }

    return res.json();
  },

  // ---- Auth ----

  async setup(password) {
    return this._fetch("/api/auth/setup", {
      method: "POST",
      body: JSON.stringify({ password }),
    });
  },

  async login(username, password) {
    return this._fetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  },

  async logout() {
    return this._fetch("/api/auth/logout", { method: "POST" });
  },

  async changePassword(oldPassword, newPassword) {
    return this._fetch("/api/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
    });
  },

  async me() {
    return this._fetch("/api/auth/me");
  },

  // ---- Status ----

  async getStatus() {
    return this._fetch("/api/status");
  },

  async getLatestMeasurements(limit = 20) {
    return this._fetch(`/api/measurements/latest?limit=${limit}`);
  },

  // ---- Config ----

  async getConfig() {
    return this._fetch("/api/config");
  },

  async exportConfig() {
    return this._fetch("/api/config/export", { method: "POST" });
  },
};
