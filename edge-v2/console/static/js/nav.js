// PlantOS Edge v2 — Navigation sidebar injection

const NAV = {
  /** Navigation items definition */
  items: [
    { id: "dashboard", label: "Dashboard", icon: "📊", href: "/dashboard.html" },
    { id: "signals", label: "Signals", icon: "📡", href: "/signals.html" },
    { id: "sync", label: "Sync Status", icon: "🔄", href: "/sync.html" },
    { id: "logs", label: "Logs", icon: "📋", href: "/logs.html" },
    { id: "settings", label: "Settings", icon: "⚙️", href: "/settings.html" },
  ],

  /** Get current page ID from URL */
  getCurrentPage() {
    const path = window.location.pathname;
    const match = path.match(/\/(\w+)\.html/);
    return match ? match[1] : "dashboard";
  },

  /** Render and inject the sidebar */
  render() {
    const current = this.getCurrentPage();
    const sidebar = document.getElementById("sidebar");
    if (!sidebar) return;

    sidebar.innerHTML = `
      <div class="sidebar-header">
        <div>
          <div class="sidebar-logo">PlantOS <span class="sidebar-logo-sub">Edge Lite</span></div>
        </div>
      </div>
      <nav class="sidebar-nav">
        ${this.items.map(item => `
          <a class="nav-item ${item.id === current ? "active" : ""}"
             href="${item.href}">
            <span class="nav-icon">${item.icon}</span>
            ${item.label}
          </a>
        `).join("")}
      </nav>
      <div class="sidebar-footer">
        <a class="nav-item" href="#" onclick="Auth.logout(); return false;">
          <span class="nav-icon">🚪</span>
          Logout
        </a>
      </div>
    `;
  },
};

// Auto-render on page load
document.addEventListener("DOMContentLoaded", () => NAV.render());
