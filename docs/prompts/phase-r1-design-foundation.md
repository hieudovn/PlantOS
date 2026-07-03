# Phase R1 — Design Foundation

## Context

You are the Coder-Executioner for PlantOS Center UI Redesign Phase R1.

The PM has approved the redesign strategy. Phase R1 establishes the visual foundation before any page changes: CSS tokens, icons, badges, and header cleanup.

**Key constraint:** Do NOT change any page content, routes, or API calls. Only touch Sidebar, Topbar, and add new files.

## Required Reading

```text
docs/design/center-ui-pm-decision.md          ← PM decision document
docs/design/center-ui-redesign-plan.md        ← Redesign plan
frontend/src/components/layout/Sidebar.tsx    ← Current sidebar (emoji icons)
frontend/src/components/layout/Topbar.tsx     ← Current topbar (MVP Preview)
frontend/src/styles/globals.css               ← Global styles
```

---

## Task R1.1 — Create `tokens.css`

Create `frontend/src/styles/tokens.css`:

```css
/* PlantOS Design Tokens — Dark Theme (default) */
:root {
  /* Surfaces */
  --surface-primary: #0f172a;
  --surface-secondary: #1e293b;
  --surface-card: #1e293b;
  --surface-hover: #334155;

  /* Text */
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;

  /* Borders */
  --border-default: #334155;
  --border-subtle: #1e293b;

  /* Status */
  --status-normal: #22c55e;
  --status-warning: #eab308;
  --status-critical: #ef4444;
  --status-offline: #6b7280;
  --status-simulated: #a855f7;

  /* Data Quality */
  --quality-good: #22c55e;
  --quality-uncertain: #eab308;
  --quality-bad: #ef4444;
  --quality-stale: #6b7280;

  /* Accent */
  --accent-primary: #3b82f6;
  --accent-secondary: #06b6d4;
}
```

Import into `globals.css` at the top:
```css
@import './tokens.css';
```

Verify: Open browser DevTools → `:root` should show all CSS variables.

---

## Task R1.2 — Replace Emoji Icons with Lucide

In `frontend/src/components/layout/Sidebar.tsx`, replace ALL emoji with Lucide icons:

| Current (emoji text) | Replace with (Lucide import) |
|----------------------|------------------------------|
| `🏭` | `LayoutDashboard` from `lucide-react` |
| `📋` | `Boxes` from `lucide-react` |
| `📡` | `Activity` from `lucide-react` |
| `📈` | `LineChart` from `lucide-react` |
| `🗺️` | `Workflow` from `lucide-react` |
| `🌍` | `MapPin` from `lucide-react` |
| `🚨` | `Bell` from `lucide-react` |
| `🖥️` | `Server` from `lucide-react` |

Change each icon from:
```tsx
<span>{icon}</span>  {/* emoji */}
```
To:
```tsx
<LayoutDashboard className="w-4 h-4" />  {/* Lucide */}
```

Keep the same `className` for sizing. Icon size: `w-4 h-4` for nav items, `w-5 h-5` for the PlantOS logo area.

**Do NOT change** the navigation structure, routes, or link behavior. Only the icon rendering.

---

## Task R1.3 — Create DataQualityBadge Component

Create `frontend/src/components/industrial/DataQualityBadge.tsx`:

```tsx
import { Circle } from "lucide-react";

type Props = {
  quality: string;     // "GOOD" | "UNCERTAIN" | "BAD" | "STALE" | "SIMULATED"
  timestamp?: string;  // ISO 8601
  className?: string;
};

function timeAgo(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

const qualityConfig: Record<string, { color: string; label: string }> = {
  GOOD: { color: "var(--quality-good)", label: "Good" },
  UNCERTAIN: { color: "var(--quality-uncertain)", label: "Uncertain" },
  BAD: { color: "var(--quality-bad)", label: "Bad" },
  STALE: { color: "var(--quality-stale)", label: "Stale" },
  SIMULATED: { color: "var(--status-simulated)", label: "Simulated" },
};

export function DataQualityBadge({ quality, timestamp, className = "" }: Props) {
  const cfg = qualityConfig[quality] || qualityConfig.UNCERTAIN;
  return (
    <span className={`inline-flex items-center gap-1 text-xs ${className}`}>
      <Circle className="w-2 h-2 fill-current" style={{ color: cfg.color }} />
      <span style={{ color: cfg.color }}>{cfg.label}</span>
      {timestamp && (
        <span className="text-gray-500">· {timeAgo(timestamp)}</span>
      )}
    </span>
  );
}
```

Create directory `frontend/src/components/industrial/` if not exists.

---

## Task R1.4 — Replace "MVP Preview" with Version Badge

In `frontend/src/components/layout/Topbar.tsx`, find the text `"MVP Preview"` and replace with:

```tsx
<span className="text-xs text-gray-600 border border-gray-700 rounded px-1.5 py-0.5 font-mono">
  v0.1.0
</span>
```

Keep the same position in the header (right side, next to user/logout).

---

## Task R1.5 — Refactor Topbar & Sidebar with Tokens

Replace hardcoded Tailwind color classes with CSS token references:

**Sidebar.tsx:**
- `bg-gray-950` → `style={{ backgroundColor: 'var(--surface-primary)' }}`
- `border-gray-800` → `style={{ borderColor: 'var(--border-default)' }}`
- `text-gray-400` → `style={{ color: 'var(--text-secondary)' }}`

**Topbar.tsx:**
- `bg-gray-900/50` → `style={{ backgroundColor: 'var(--surface-secondary)' }}`
- `border-gray-800` → `style={{ borderColor: 'var(--border-default)' }}`

**Rule:** Keep the Tailwind classes for layout (flex, gap, padding, etc.) — only replace COLOR classes.

---

## Verification

After all 5 tasks, open the browser:

- [ ] Sidebar icons are Lucide line icons (not emoji)
- [ ] Topbar shows `v0.1.0` (not "MVP Preview")
- [ ] DevTools → `:root` shows all CSS variables
- [ ] All pages still load and navigate correctly
- [ ] Colors look identical to before (tokens match old hardcoded values)
- [ ] No console errors

## Deliverables

1. `frontend/src/styles/tokens.css` — New file
2. `frontend/src/styles/globals.css` — Add `@import './tokens.css'`
3. `frontend/src/components/industrial/DataQualityBadge.tsx` — New file
4. `frontend/src/components/layout/Sidebar.tsx` — Icon + token refactor
5. `frontend/src/components/layout/Topbar.tsx` — Version badge + token refactor

## Files NOT to touch

- ❌ Any page component (`features/*`)
- ❌ API layer (`lib/api.ts`)
- ❌ Router, Shell, ProtectedRoute
- ❌ Backend, Edge Agent
