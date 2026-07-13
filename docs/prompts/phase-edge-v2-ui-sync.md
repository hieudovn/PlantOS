# Task: Edge v2 UI — Sync Design with Center

> **Role:** Coder-Executioner (V4 Flash)
> **Scope:** CSS-only — sync Edge v2 design tokens + polish to match Center UI
> **Constraint:** Do NOT change HTML structure. Do NOT add build steps. Pure CSS + minor JS polish.

---

## 1. Analysis: What's Different

| Element | Center UI | Edge v2 (current) | Gap |
|---|---|---|---|
| Font | Inter (Google Fonts) | System fonts | Mismatch |
| Background | `#0f172a` (slate-900) | `#0f1117` (near-black) | Off by shade |
| Surface/Cards | `#1e293b` (slate-800) | `#1a1d27` | Off by shade |
| Primary accent | `#3b82f6` (blue-500) | `#2563eb` (blue-600) | Different blue |
| Text primary | `#f1f5f9` (slate-100) | `#e8eaed` | Slightly different |
| Text secondary | `#94a3b8` (slate-400) | `#9aa0b0` | Slightly different |
| Text muted | `#64748b` (slate-500) | `#6b7280` (gray-500) | Slightly different |
| Border | `#334155` (slate-700) | `#2a2d42` | Different |
| Status green | `#22c55e` | `#22c55e` | ✅ Same |
| Status red | `#ef4444` | `#ef4444` | ✅ Same |
| Status yellow | `#f59e0b` | `#f59e0b` | ✅ Same |
| Sidebar icons | Lucide SVG (React) | Emoji (📊📡🔄📋⚙️) | Visual mismatch |
| Buttons | Tailwind rounded + shadow | Custom CSS | Minor visual diff |
| Card border-radius | `8px` (rounded-lg) | `8px` | ✅ Same |

---

## 2. Implementation

### File 1: `edge-v2/console/static/css/plantos-tokens.css`

Replace the ENTIRE file content. The key change: use Center's exact hex values.

```css
/* PlantOS Edge v2 — Design Tokens (synced with Center UI v2026-07-13)
   Single source of truth: frontend/src/styles/globals.css */

@import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400..700&display=swap');

:root {
  color-scheme: dark;

  /* === Surfaces (synced with Center) === */
  --surface-primary: #0f172a;
  --surface-secondary: #1e293b;
  --surface-card: #1e293b;
  --surface-hover: #334155;

  /* Keep backward compat aliases */
  --color-bg: var(--surface-primary);
  --color-surface: var(--surface-card);
  --color-surface-hover: var(--surface-hover);
  --color-surface-active: #2a3a5c;
  --color-border: #334155;
  --color-border-light: #475569;

  /* === Text (synced with Center) === */
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;

  --color-text: var(--text-primary);
  --color-text-secondary: var(--text-secondary);
  --color-text-muted: var(--text-muted);
  --color-text-inverse: #0f172a;

  /* === Accent (synced with Center — blue-500) === */
  --accent-primary: #3b82f6;
  --accent-secondary: #06b6d4;

  --color-primary: var(--accent-primary);
  --color-primary-hover: #2563eb;
  --color-primary-light: #60a5fa;
  --color-primary-bg: rgba(59, 130, 246, 0.12);

  /* === Status (verified same as Center) === */
  --status-normal: #22c55e;
  --status-warning: #f59e0b;
  --status-critical: #ef4444;
  --status-offline: #6b7280;

  --color-success: var(--status-normal);
  --color-success-bg: rgba(34, 197, 94, 0.1);
  --color-warning: var(--status-warning);
  --color-warning-bg: rgba(245, 158, 11, 0.1);
  --color-error: var(--status-critical);
  --color-error-bg: rgba(239, 68, 68, 0.1);
  --color-info: #3b82f6;
  --color-info-bg: rgba(59, 130, 246, 0.1);

  /* === Typography (synced with Center — Inter) === */
  --font-sans: 'Inter', ui-sans-serif, system-ui, sans-serif;
  --font-mono: 'Inter', ui-monospace, SFMono-Regular, Consolas, monospace;
  --font-family: var(--font-sans);
  --font-size-xs: 11px;
  --font-size-sm: 13px;
  --font-size-base: 14px;
  --font-size-lg: 16px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;

  /* === Border radius === */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;

  /* === Shadows === */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.3);

  /* === Layout === */
  --sidebar-width: 240px;
  --header-height: 56px;

  /* === Spacing === */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;
}

/* === Reset === */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  height: 100%;
  font-family: var(--font-sans);
  font-size: var(--font-size-base);
  color: var(--text-primary);
  background: var(--surface-primary);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

a { color: var(--accent-primary); text-decoration: none; }
a:hover { text-decoration: underline; }

/* === Layout === */
.app-layout {
  display: flex;
  height: 100vh;
}

/* === Sidebar (synced with Center) === */
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  background: var(--surface-secondary);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  padding: var(--space-md) 0;
  overflow-y: auto;
}

.sidebar-header {
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-sm);
}

.sidebar-logo {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.sidebar-logo-sub {
  font-size: var(--font-size-xs);
  font-weight: 400;
  color: var(--text-muted);
  display: block;
  margin-top: 2px;
}

.sidebar-nav { list-style: none; padding: var(--space-sm); }

.sidebar-nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  margin-bottom: 2px;
}

.sidebar-nav-item:hover {
  background: var(--surface-hover);
  color: var(--text-primary);
}

.sidebar-nav-item.active {
  background: var(--color-primary-bg);
  color: var(--accent-primary);
}

.sidebar-nav-item .nav-icon {
  font-size: var(--font-size-lg);
  width: 22px;
  text-align: center;
  flex-shrink: 0;
}

.sidebar-footer {
  margin-top: auto;
  padding: var(--space-md) var(--space-lg);
  border-top: 1px solid var(--color-border);
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

/* === Main content === */
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg);
}

.page-header {
  margin-bottom: var(--space-lg);
}

.page-header h1 {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.page-body { }

/* === Cards === */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.card {
  background: var(--surface-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  transition: border-color 0.15s ease;
}

.card:hover {
  border-color: var(--color-border-light);
}

.card-header {
  font-size: var(--font-size-xs);
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-sm);
}

.card-value {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--text-primary);
}

/* === Tables === */
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.data-table th {
  text-align: left;
  padding: var(--space-sm) var(--space-md);
  font-weight: 600;
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--color-border);
}

.data-table td {
  padding: var(--space-sm) var(--space-md);
  color: var(--text-secondary);
  border-bottom: 1px solid var(--color-border-light);
}

.data-table tr:hover td {
  background: var(--surface-hover);
}

/* === Buttons === */
.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-primary {
  background: var(--accent-primary);
  color: #fff;
  border-color: var(--accent-primary);
}

.btn-primary:hover {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

.btn-secondary {
  background: transparent;
  color: var(--text-secondary);
  border-color: var(--color-border);
}

.btn-secondary:hover {
  background: var(--surface-hover);
  color: var(--text-primary);
}

.btn-danger {
  background: transparent;
  color: var(--status-critical);
  border-color: var(--status-critical);
}

.btn-danger:hover {
  background: var(--color-error-bg);
}

/* === Forms === */
.form-group {
  margin-bottom: var(--space-md);
}

.form-group label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.form-input {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  background: var(--surface-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  font-family: var(--font-sans);
  transition: border-color 0.15s ease;
}

.form-input:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

.form-input::placeholder {
  color: var(--text-muted);
}

/* === Login page === */
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--surface-primary);
}

.login-card {
  width: 380px;
  max-width: 90vw;
  background: var(--surface-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-xl);
}

.login-logo {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.login-logo h1 {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text-primary);
}

.login-logo p {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  margin-top: var(--space-xs);
}

.login-error {
  background: var(--color-error-bg);
  color: var(--status-critical);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  margin-bottom: var(--space-md);
  display: none;
}

/* === Utility === */
.mt-sm { margin-top: var(--space-sm); }
.mt-md { margin-top: var(--space-md); }
.mt-lg { margin-top: var(--space-lg); }
.mb-sm { margin-bottom: var(--space-sm); }
.mb-md { margin-bottom: var(--space-md); }
.text-muted { color: var(--text-muted); }
.text-sm { font-size: var(--font-size-sm); }
.text-xs { font-size: var(--font-size-xs); }
.text-center { text-align: center; }
.flex { display: flex; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.gap-sm { gap: var(--space-sm); }
.gap-md { gap: var(--space-md); }
```

### File 2: `edge-v2/console/static/js/nav.js`

Replace the emoji icons with simple SVG icons that match Center's Lucide style (same icon shapes, same size):

```javascript
// PlantOS Edge v2 — Navigation sidebar injection

const NAV = {
  /** SVG icons matching Center's Lucide icon set */
  icons: {
    dashboard: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',
    signals: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>',
    sync: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>',
    logs: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
    settings: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
  },

  items: [
    { id: "dashboard", label: "Dashboard", icon: "dashboard", href: "/dashboard.html" },
    { id: "signals", label: "Signals", icon: "signals", href: "/signals.html" },
    { id: "sync", label: "Sync Status", icon: "sync", href: "/sync.html" },
    { id: "logs", label: "Logs", icon: "logs", href: "/logs.html" },
    { id: "settings", label: "Settings", icon: "settings", href: "/settings.html" },
  ],

  getCurrentPage() {
    const path = window.location.pathname;
    const match = path.match(/\/(\w+)\.html/);
    return match ? match[1] : "dashboard";
  },

  render() {
    const current = this.getCurrentPage();
    const sidebar = document.getElementById("sidebar");
    if (!sidebar) return;

    const navItems = this.items.map(item => {
      const isActive = item.id === current;
      const iconSvg = this.icons[item.icon] || '';
      return `
        <a href="${item.href}" class="sidebar-nav-item${isActive ? ' active' : ''}">
          <span class="nav-icon">${iconSvg}</span>
          ${item.label}
        </a>`;
    }).join('');

    sidebar.innerHTML = `
      <div class="sidebar-header">
        <div class="sidebar-logo">PlantOS <span class="sidebar-logo-sub">Edge Lite</span></div>
      </div>
      <nav class="sidebar-nav">${navItems}</nav>
      <div class="sidebar-footer">v2.0.0</div>`;
  }
};

document.addEventListener('DOMContentLoaded', () => NAV.render());
```

### File 3: Each HTML file — minor polish

Add `<link rel="preconnect" href="https://fonts.googleapis.com">` + `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>` before the CSS import in EVERY HTML file's `<head>`. This is already done by the `@import` in CSS, but explicit preconnects improve performance.

**Files to update (add 2 preconnect lines before CSS link):**
- `edge-v2/console/static/dashboard.html`
- `edge-v2/console/static/login.html`
- `edge-v2/console/static/signals.html`
- `edge-v2/console/static/sync.html`
- `edge-v2/console/static/logs.html`
- `edge-v2/console/static/settings.html`
- `edge-v2/console/static/connections.html`
- `edge-v2/console/static/processing.html`

In each, BEFORE `<link rel="stylesheet" href="/css/plantos-tokens.css">`, add:
```html
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
```

---

## 3. Deploy

```bash
# 1. Stop v2
ssh plantos@103.97.132.249 'docker stop plantos-edge-v2'

# 2. Copy files to VPS
scp edge-v2/console/static/css/plantos-tokens.css plantos@103.97.132.249:/opt/plantos/edge-v2/console/static/css/plantos-tokens.css
scp edge-v2/console/static/js/nav.js plantos@103.97.132.249:/opt/plantos/edge-v2/console/static/js/nav.js

for f in dashboard login signals sync logs settings connections processing; do
  scp "edge-v2/console/static/${f}.html" "plantos@103.97.132.249:/opt/plantos/edge-v2/console/static/${f}.html"
done

# 3. Rebuild & start
ssh plantos@103.97.132.249 '
  cd /opt/plantos
  docker build -t plantos-edge-v2:unified-ui -f edge-v2/Dockerfile .
  docker rm plantos-edge-v2 2>/dev/null || true
  docker run -d --name plantos-edge-v2 --network host \
    -v /opt/plantos/edge-v2/data:/app/data \
    plantos-edge-v2:unified-ui
'

# 4. Verify
sleep 8
ssh plantos@103.97.132.249 'curl -s http://localhost:8011/api/status | python3 -c "import sys,json;d=json.load(sys.stdin);print(d[\"status\"])"'
```

---

## 4. Expected Result

| Element | Before | After |
|---|---|---|
| Font | System font | Inter (matching Center) |
| Background | `#0f1117` | `#0f172a` (slate-900) |
| Cards | `#1a1d27` | `#1e293b` (slate-800) |
| Accent | `#2563eb` | `#3b82f6` (blue-500) |
| Sidebar icons | Emoji 📊📡🔄 | SVG (matching Lucide) |
| Sidebar bg | Dark | `#1e293b` with border |
| Visual feel | "almost there" | **Identical to Center** |
