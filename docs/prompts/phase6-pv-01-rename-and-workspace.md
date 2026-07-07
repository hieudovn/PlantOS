# Phase 6-PV-01 — Rename Diagrams → Operations & Workspace Foundation

> **Phase:** 6-PV-01 (Industrial Hardening — Process View)  
> **Parent:** Phase 6, per `docs/90-roadmap.md`  
> **Design spec:** `docs/phase-ui-process-view-plan.md`  
> **Effort:** 3-4h

---

## Objective

Rename the `Diagrams` module to `Operations`, create the Process View workspace shell with breadcrumb, hierarchy panel, main canvas, and context panel.

---

## Task 1: Rename Sidebar Navigation

**File:** `frontend/src/components/layout/Sidebar.tsx`

1. Change Monitor group item:
   - Old: `{ path: "/diagrams", icon: Workflow, label: "Diagrams" }`
   - New: `{ path: "/operations", icon: Factory, label: "Operations" }`
2. Import `Factory` from `lucide-react` (remove `Workflow` if no longer used elsewhere — it's still used in WorkflowDiagram component, so keep both)

---

## Task 2: Add Routes

**File:** `frontend/src/routes/index.tsx`

1. Add import: `import { ProcessViewWorkspace } from "@/features/operations/ProcessViewWorkspace";`
2. Add route:
   ```tsx
   { path: "operations", element: <ProcessViewWorkspace /> },
   { path: "operations/area/:areaId", element: <ProcessViewWorkspace /> },
   { path: "operations/asset/:assetId", element: <ProcessViewWorkspace /> },
   ```
3. Keep OLD route for backward compatibility:
   ```tsx
   { path: "diagrams", element: <DiagramPage /> },  // Keep — don't delete
   ```
   Do NOT remove the existing `{ path: "diagrams", element: <DiagramPage /> }` — old links still work.

---

## Task 3: Create ProcessViewWorkspace Shell

**New file:** `frontend/src/features/operations/ProcessViewWorkspace.tsx`

Layout:
```
┌─────────────────────────────────────────────┐
│ Breadcrumb: Plant > Area > Asset            │ ← BreadcrumbNav
├──────────┬──────────────────┬───────────────┤
│ Hierarchy│                  │  Context      │
│ Panel    │  Main Canvas     │  Panel        │
│ (240px)  │  (flex-1)        │  (320px)      │
│          │                  │  collapsible  │
├──────────┴──────────────────┴───────────────┤
│ Overlay Bar: [Status] [Alarm] [Quality]     │ ← placeholder
└─────────────────────────────────────────────┘
```

Implementation:
```tsx
import { useParams } from "react-router-dom";
import { HierarchyPanel } from "./components/HierarchyPanel";
import { BreadcrumbNav } from "./components/BreadcrumbNav";
import { ContextPanel } from "./components/ContextPanel";
import { OverlayBar } from "./components/OverlayBar";

export function ProcessViewWorkspace() {
  const { areaId, assetId } = useParams();
  const [selectedObject, setSelectedObject] = useState<{type: string; id: string} | null>(null);
  const [contextVisible, setContextVisible] = useState(true);

  return (
    <div className="flex flex-col h-full">
      <BreadcrumbNav areaId={areaId} assetId={assetId} />
      <div className="flex flex-1 overflow-hidden">
        <HierarchyPanel onSelect={setSelectedObject} selectedId={selectedObject?.id} />
        <main className="flex-1 overflow-auto p-4" style={{ backgroundColor: 'var(--surface-primary)' }}>
          {/* Main canvas — will be filled in Phase 6-PV-02/03/04 */}
          <div className="flex items-center justify-center h-full" style={{ color: 'var(--text-muted)' }}>
            <div className="text-center">
              <p className="text-lg mb-2">Process View</p>
              <p className="text-sm">Select an area or asset from the hierarchy panel to begin monitoring.</p>
            </div>
          </div>
        </main>
        {contextVisible && (
          <ContextPanel object={selectedObject} onClose={() => setContextVisible(false)} />
        )}
      </div>
      <OverlayBar />
    </div>
  );
}
```

---

## Task 4: Create HierarchyPanel

**New file:** `frontend/src/features/operations/components/HierarchyPanel.tsx`

- Width: `w-60` (240px), scrollable, border-right
- Fetch areas from `/api/v1/areas?plant_id={currentPlant}` using `useQuery`
- Group assets by area_id
- Render tree: Plant → click expand → Areas → click → Assets
- Highlight selected node
- Click area → `setSelectedObject({type: 'area', id: areaId})` + update URL to `/operations/area/:areaId`
- Click asset → `setSelectedObject({type: 'asset', id: assetId})` + update URL to `/operations/asset/:assetId`

**API calls:**
```tsx
const { data: areas } = useQuery({ queryKey: ["areas", plantId], queryFn: () => fetchAPI(`/api/v1/areas?plant_id=${plantId}`) });
const { data: assets } = useQuery({ queryKey: ["assets", plantId], queryFn: () => fetchAPI(`/api/v1/assets?plant_id=${plantId}`) });
```

**Props:**
```tsx
interface Props {
  onSelect: (obj: {type: string; id: string} | null) => void;
  selectedId?: string;
}
```

Use `fetchAPI` from `@/lib/api` (already exported). Import `useWorkspace` for plantId. Import `useNavigate` for URL navigation.

Style: dark theme, `var(--surface-primary)` background, `var(--border-default)` borders. Tree nodes with `var(--text-secondary)` text, `var(--surface-hover)` on hover/selected.

---

## Task 5: Create BreadcrumbNav

**New file:** `frontend/src/features/operations/components/BreadcrumbNav.tsx`

- Height: `h-10` (40px)
- Background: `var(--surface-secondary)`, border-bottom
- Display: `WTP-DEMO-01 > Filtration Area > FILTER-101`
- Each segment is a clickable link:
  - Plant name → `/operations`
  - Area name → `/operations/area/:areaId`
  - Asset name → `/operations/asset/:assetId`
- Use `ChevronRight` icon between segments

**Props:**
```tsx
interface Props {
  areaId?: string;
  assetId?: string;
}
```

Fetch area/asset names from API using the IDs. If no areaId/assetId, show only plant name.

---

## Task 6: Create ContextPanel (placeholder)

**New file:** `frontend/src/features/operations/components/ContextPanel.tsx`

- Width: `w-80` (320px), border-left, scrollable
- Background: `var(--surface-card)`
- Header: object name + close button (X icon)
- Content: placeholder text "Select an object to view details"
- When `object` is set (from HierarchyPanel click), display:
  - Object type badge (Area / Asset)
  - Object ID + name
  - "KPIs and trends will appear here in Phase 6-PV-04"
- Will be fully implemented in Phase 6-PV-04

**Props:**
```tsx
interface Props {
  object: {type: string; id: string} | null;
  onClose: () => void;
}
```

---

## Task 7: Create OverlayBar (placeholder)

**New file:** `frontend/src/features/operations/components/OverlayBar.tsx`

- Height: `h-10` (40px)
- Background: `var(--surface-secondary)`, border-top
- Horizontal button bar with toggle buttons:
  ```
  [Status ●] [Alarm ▲] [Quality ◇]
  ```
- Each button: active/inactive state with color indicator
- Status: green dot when active
- Alarm: red dot when active
- Quality: yellow dot when active
- All inactive for now (will be wired in Phase 6-PV-02+)
- Styling: small text buttons with rounded borders, `var(--text-muted)` when inactive, accent color when active

---

## Task 8: Create operations feature directory structure

Create these files (some as empty placeholders for future phases):
```
frontend/src/features/operations/
├── ProcessViewWorkspace.tsx     (Task 3 — implemented)
├── PlantOverviewView.tsx        (empty placeholder — Phase 6-PV-02)
├── AreaMonitoringView.tsx       (empty placeholder — Phase 6-PV-03)
├── AssetConditionView.tsx       (empty placeholder — Phase 6-PV-04)
├── components/
│   ├── HierarchyPanel.tsx       (Task 4 — implemented)
│   ├── BreadcrumbNav.tsx        (Task 5 — implemented)
│   ├── ContextPanel.tsx         (Task 6 — placeholder)
│   ├── OverlayBar.tsx           (Task 7 — placeholder)
│   └── ProcessBlock.tsx         (empty — Phase 6-PV-02)
├── config/
│   └── wtp-workflow.ts          (empty — Phase 6-PV-02)
└── hooks/
    └── useProcessHierarchy.ts   (empty — Phase 6-PV-02)
```

---

## Task 9: Update API exports

**File:** `frontend/src/lib/api.ts`

Verify that `fetchAPI` is exported (it should already be — it was exported in a previous phase). If not, add `export` keyword.

---

## Validation

After implementation, verify:

1. ✅ Sidebar shows "Operations" (not "Diagrams") with Factory icon
2. ✅ Visiting `/diagrams` still works (shows old DiagramPage)
3. ✅ Visiting `/operations` shows the new workspace shell
4. ✅ Hierarchy panel shows areas and assets from WTP-DEMO-01
5. ✅ Clicking area/asset updates breadcrumb + URL
6. ✅ Context panel opens/closes
7. ✅ Overlay bar shows toggle buttons
8. ✅ No TypeScript errors, `npm run build` succeeds
9. ✅ Dark theme consistent with existing pages
10. ✅ Backward compatible — all existing routes still work

---

## Reference Files

- `docs/phase-ui-process-view-plan.md` — Full design spec
- `docs/90-roadmap.md` — Phase 6 context
- `frontend/src/components/layout/Sidebar.tsx` — Navigation
- `frontend/src/routes/index.tsx` — Route definitions
- `frontend/src/lib/api.ts` — API client
- `frontend/src/lib/WorkspaceContext.tsx` — Plant context
