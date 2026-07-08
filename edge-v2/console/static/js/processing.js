// PlantOS Edge v2 — Processing profiles API integration

const ProcessingAPI = {
  async listProfiles() {
    return API._fetch("/api/processing/profiles");
  },

  async getProfile(id) {
    return API._fetch(`/api/processing/profiles/${id}`);
  },

  async createProfile(data) {
    return API._fetch("/api/processing/profiles", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateProfile(id, data) {
    return API._fetch(`/api/processing/profiles/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  async deleteProfile(id) {
    return API._fetch(`/api/processing/profiles/${id}`, {
      method: "DELETE",
    });
  },

  async previewProfile(id, rawSamples) {
    return API._fetch(`/api/processing/profiles/${id}/preview`, {
      method: "POST",
      body: JSON.stringify({ raw_samples: rawSamples }),
    });
  },

  async getStepTypes() {
    return API._fetch("/api/processing/step-types");
  },

  async assignProfile(signalId, profileId) {
    return API._fetch("/api/processing/assign", {
      method: "POST",
      body: JSON.stringify({ signal_id: signalId, profile_id: profileId }),
    });
  },

  async getAssignment(signalId) {
    return API._fetch(`/api/processing/assign?signal_id=${encodeURIComponent(signalId)}`);
  },
};
