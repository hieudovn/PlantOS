// PlantOS Edge v2 — Connection management and wizard API integration

const Connections = {
  /** Fetch all connectors with status */
  async list() {
    return API._fetch("/api/connections");
  },

  /** Get a single connector detail */
  async get(id) {
    return API._fetch(`/api/connections/${id}`);
  },

  /** Create a draft connector */
  async create(data) {
    return API._fetch("/api/connections", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /** Update draft config */
  async update(id, data) {
    return API._fetch(`/api/connections/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  /** Validate draft */
  async validate(id) {
    return API._fetch(`/api/connections/${id}/validate`, { method: "POST" });
  },

  /** Test connection */
  async test(id) {
    return API._fetch(`/api/connections/${id}/test`, { method: "POST" });
  },

  /** Apply draft → active */
  async apply(id) {
    return API._fetch(`/api/connections/${id}/apply`, { method: "POST" });
  },

  /** Confirm apply success/failure */
  async confirm(id, success) {
    return API._fetch(`/api/connections/${id}/confirm`, {
      method: "POST",
      body: JSON.stringify({ success }),
    });
  },

  /** Rollback to previous config */
  async rollback(id) {
    return API._fetch(`/api/connections/${id}/rollback`, { method: "POST" });
  },

  /** Start connector */
  async start(id) {
    return API._fetch(`/api/connections/${id}/start`, { method: "POST" });
  },

  /** Stop connector */
  async stop(id) {
    return API._fetch(`/api/connections/${id}/stop`, { method: "POST" });
  },

  /** Restart connector */
  async restart(id) {
    return API._fetch(`/api/connections/${id}/restart`, { method: "POST" });
  },

  /** List tags */
  async listTags(id) {
    return API._fetch(`/api/connections/${id}/tags`);
  },

  /** Add/update tag */
  async saveTag(id, tag) {
    return API._fetch(`/api/connections/${id}/tags`, {
      method: "POST",
      body: JSON.stringify(tag),
    });
  },

  /** Delete tag */
  async deleteTag(connId, tagId) {
    return API._fetch(`/api/connections/${connId}/tags/${tagId}`, {
      method: "DELETE",
    });
  },

  /** Browse OPC UA address space */
  async browse(id, path) {
    const qs = path ? `?path=${encodeURIComponent(path)}` : "";
    return API._fetch(`/api/connections/${id}/browse${qs}`);
  },

  /** Import tags CSV */
  async importCsv(id, csvText) {
    return API._fetch(`/api/connections/${id}/tags/import`, {
      method: "POST",
      headers: { "Content-Type": "text/csv" },
      body: csvText,
    });
  },

  /** Get export CSV URL */
  getExportUrl(id) {
    return `/api/connections/${id}/tags/export`;
  },
};
