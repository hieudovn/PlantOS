// PlantOS Edge v2 — Auth check and login state management

const Auth = {
  /** Check if user is authenticated. Redirects to login if not. */
  async requireAuth() {
    try {
      const user = await API.me();
      return user;
    } catch {
      window.location.href = "/login.html";
      return null;
    }
  },

  /** Check first-run status. Returns true if setup needed. */
  async isFirstRun() {
    try {
      const status = await API.getStatus();
      return status.first_run === true;
    } catch {
      return false;
    }
  },

  /** Log out and redirect to login */
  async logout() {
    try {
      await API.logout();
    } catch {
      // Ignore errors
    }
    window.location.href = "/login.html";
  },
};
