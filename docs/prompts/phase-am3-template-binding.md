# Phase AM-3 — Asset Template + Signal Binding

> **Phase:** AM-3 (Asset Model Builder)  
> **Depends on:** AM-2 (asset CRUD complete)  
> **Effort:** 3-4h  

---

## Objective

Define asset templates with attributes, and bind real signals to asset attributes. This makes asset creation structured instead of ad-hoc.

---

## Task 1: Migration 006 — Asset Templates & Bindings

**File:** `backend/migrations/versions/006_asset_templates.py`

Create via Alembic:
```bash
cd backend && alembic revision --autogenerate -m "asset_templates"
```

OR write manually:

```sql
CREATE TABLE asset_templates (
    template_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    asset_type VARCHAR(64) NOT NULL,
    asset_role VARCHAR(32) NOT NULL DEFAULT 'equipment',
    description TEXT,
    attributes_json JSONB NOT NULL DEFAULT '[]',
    domain_type VARCHAR(32) DEFAULT 'generic',
    metadata_json JSONB DEFAULT '{}',
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE asset_attribute_bindings (
    binding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(128) NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    template_id VARCHAR(64) REFERENCES asset_templates(template_id),
    attribute_name VARCHAR(128) NOT NULL,
    signal_id VARCHAR(256) REFERENCES signals(signal_id) ON DELETE SET NULL,
    binding_type VARCHAR(32) NOT NULL DEFAULT 'direct',
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    validation_status VARCHAR(32),
    validation_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(asset_id, attribute_name)
);

CREATE INDEX idx_bindings_asset ON asset_attribute_bindings(asset_id);
CREATE INDEX idx_bindings_signal ON asset_attribute_bindings(signal_id);
```

Run on VPS after deploy: `docker exec plantos-backend alembic upgrade head`

---

## Task 2: ORM Models

**New file:** `backend/app/modules/asset_templates/models.py`

```python
"""Asset Template & Binding — SQLAlchemy models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

def _utcnow(): return datetime.now(timezone.utc)
def _new_uuid(): return uuid.uuid4()

class AssetTemplate(Base):
    __tablename__ = "asset_templates"
    
    template_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False)
    asset_role: Mapped[str] = mapped_column(String(32), default="equipment")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    attributes_json: Mapped[dict | list] = mapped_column(JSON, default=list)
    domain_type: Mapped[str] = mapped_column(String(32), default="generic")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class AssetAttributeBinding(Base):
    __tablename__ = "asset_attribute_bindings"
    __table_args__ = (UniqueConstraint("asset_id", "attribute_name"),)
    
    binding_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    asset_id: Mapped[str] = mapped_column(String(128), ForeignKey("assets.asset_id", ondelete="CASCADE"), nullable=False)
    template_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("asset_templates.template_id"), nullable=True)
    attribute_name: Mapped[str] = mapped_column(String(128), nullable=False)
    signal_id: Mapped[str | None] = mapped_column(String(256), ForeignKey("signals.signal_id", ondelete="SET NULL"), nullable=True)
    binding_type: Mapped[str] = mapped_column(String(32), default="direct")
    status: Mapped[str] = mapped_column(String(32), default="active")
    validation_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    validation_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
```

Add to `backend/app/modules/__init__.py`:
```python
from app.modules.asset_templates.models import AssetTemplate, AssetAttributeBinding  # noqa: F401
```

Create `backend/app/modules/asset_templates/__init__.py` (empty).

---

## Task 3: Backend — Template CRUD API

**New file:** `backend/app/modules/asset_templates/router.py`

```
POST   /api/v1/asset-templates              Create template
GET    /api/v1/asset-templates              List all
GET    /api/v1/asset-templates/{id}         Get one
PATCH  /api/v1/asset-templates/{id}         Update
DELETE /api/v1/asset-templates/{id}         Delete
POST   /api/v1/asset-templates/seed         Seed default templates
```

### Schemas (same file or new `schemas.py`):

```python
from pydantic import BaseModel, Field
from typing import Optional

class TemplateAttribute(BaseModel):
    name: str
    display_name: Optional[str] = None
    required: bool = False
    data_type: str = "float"
    unit: Optional[str] = None
    category: str = "measurement"

class TemplateCreate(BaseModel):
    template_id: str
    name: str
    asset_type: str
    asset_role: str = "equipment"
    description: Optional[str] = None
    attributes: list[TemplateAttribute] = []
    domain_type: str = "generic"

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    attributes: Optional[list[TemplateAttribute]] = None
    status: Optional[str] = None

class TemplateResponse(BaseModel):
    template_id: str
    name: str
    asset_type: str
    asset_role: str
    description: Optional[str] = None
    attributes: list[dict]
    domain_type: str
    version: int
    status: str
    created_at: str
    updated_at: str
```

### Seed endpoint (`POST /api/v1/asset-templates/seed`):

Create 6 default templates:

| Template | asset_type | Key Attributes |
|----------|-----------|----------------|
| `pump_template_v1` | pump | flow_rate (req), discharge_pressure (req), suction_pressure, motor_current, vibration, bearing_temperature, running_status |
| `filter_template_v1` | filter | filter_dp (req), effluent_flow (req), influent_turbidity |
| `tank_template_v1` | tank | level (req), inlet_flow, outlet_flow |
| `motor_template_v1` | motor | running_status (req), motor_current, speed, winding_temp |
| `sensor_array_template_v1` | sensor_array | (all optional — customizable) |
| `generic_equipment_template_v1` | generic | running_status (req), custom_1, custom_2, custom_3 |

Register in `backend/app/api/v1.py`:
```python
from app.modules.asset_templates.router import router as templates_router
router.include_router(templates_router, tags=["Asset Templates"])
```

---

## Task 4: Backend — Binding CRUD API

**In `backend/app/modules/asset_templates/router.py`** or separate file:

```
POST   /api/v1/assets/{asset_id}/bindings               Create/update binding
GET    /api/v1/assets/{asset_id}/bindings               List bindings for asset
DELETE /api/v1/assets/{asset_id}/bindings/{binding_id}  Remove binding
POST   /api/v1/assets/{asset_id}/bindings/validate      Validate all bindings
POST   /api/v1/assets/{asset_id}/bindings/from-template/{template_id}  Auto-generate from template
```

### BindingCreate Schema:
```python
class BindingCreate(BaseModel):
    attribute_name: str
    signal_id: Optional[str] = None
    binding_type: str = "direct"  # direct | calculated | manual | external
```

### BindingResponse Schema:
```python
class BindingResponse(BaseModel):
    binding_id: str
    asset_id: str
    template_id: Optional[str] = None
    attribute_name: str
    signal_id: Optional[str] = None
    binding_type: str
    status: str
    validation_status: Optional[str] = None
    validation_message: Optional[str] = None
```

### Auto-generate from template logic:
When `POST /assets/{id}/bindings/from-template/{template_id}` is called:
1. Load the template
2. For each attribute in `attributes_json`:
   - Create a binding record with `status="pending"` and no `signal_id`
3. Return the list of created bindings

### Validation logic (`POST /assets/{id}/bindings/validate`):
1. Load all bindings for the asset
2. For each binding:
   - If `signal_id` is set: check signal exists, signal_category matches, data_type compatible, unit compatible
   - If `signal_id` is null and attribute is required: flag as error
3. Update `validation_status` and `validation_message` on each binding
4. Return summary: `{ "valid": bool, "errors": [...], "warnings": [...] }`

---

## Task 5: Frontend — AssetDetail Bindings Tab

**File:** `frontend/src/features/assets/AssetDetail.tsx`

Add tabs to the detail view:
```tsx
const [activeTab, setActiveTab] = useState<"overview" | "bindings">("overview");
```

Tabs UI:
```tsx
<div className="flex gap-2 mb-4 border-b" style={{ borderColor: 'var(--border-default)' }}>
  <button onClick={() => setActiveTab("overview")} className={...}>Overview</button>
  <button onClick={() => setActiveTab("bindings")} className={...}>Signals / Attributes</button>
</div>
```

When `activeTab === "bindings"`, render `<AssetBindings assetId={assetId} />`.

---

## Task 6: Frontend — AssetBindings Component

**New file:** `frontend/src/features/assets/AssetBindings.tsx`

### Features:
1. Fetch bindings: `GET /api/v1/assets/{assetId}/bindings`
2. Display table: Attribute Name | Required | Bound Signal | Status | Actions
3. "Bind Signal" button → search + select signal from dropdown
4. "Unbind" button → delete binding
5. "Validate" button → call validation endpoint
6. Color coding: red=missing required, yellow=warning, green=OK

### UI Layout:
```
┌─────────────────────────────────────────────────┐
│ Signals / Attributes                    [Validate] │
├──────────────┬────────┬──────────────────┬───────┤
│ Attribute    │ Req'd  │ Bound Signal     │Status │
├──────────────┼────────┼──────────────────┼───────┤
│ flow_rate    │ Yes    │ RWP-101.flow_r.. │ ✅ OK │
│ motor_current│ No     │ —                │ ⚠️    │
│ vibration    │ No     │ —                │ —     │
└──────────────┴────────┴──────────────────┴───────┘
```

### Actions per row:
- **Bind:** opens dropdown search to select signal (filter by asset or cross-asset)
- **Unbind:** removes binding, sets signal_id to null
- **Status indicator:** green/orange/red circle + text

### API functions to add to `lib/api.ts`:
```ts
export const getBindings = (assetId: string) => fetchAPI<any[]>(`/api/v1/assets/${assetId}/bindings`);
export const createBinding = (assetId: string, data: any) => fetchAPI<any>(`/api/v1/assets/${assetId}/bindings`, { method: 'POST', body: JSON.stringify(data) });
export const deleteBinding = (assetId: string, bindingId: string) => fetchAPI(`/api/v1/assets/${assetId}/bindings/${bindingId}`, { method: 'DELETE' });
export const validateBindings = (assetId: string) => fetchAPI<any>(`/api/v1/assets/${assetId}/bindings/validate`, { method: 'POST' });
```

---

## Task 7: Frontend — Template Selector in AssetForm

**File:** `frontend/src/features/assets/AssetForm.tsx`

Add a step or field to select template after choosing asset_type:

```tsx
// After asset_type dropdown
{form.asset_type && (
  <div>
    <label>Templates for {form.asset_type}</label>
    <select value={selectedTemplate} onChange={handleTemplateChange}>
      <option value="">Custom (no template)</option>
      {templates?.filter(t => t.asset_type === form.asset_type).map(t => (
        <option key={t.template_id} value={t.template_id}>{t.name}</option>
      ))}
    </select>
  </div>
)}
```

When a template is selected and form is submitted successfully, call:
```ts
await POST /api/v1/assets/{newAssetId}/bindings/from-template/{template_id}
```

---

## Validation

```bash
# 1. Seed templates
curl -X POST http://127.0.0.1:8000/api/v1/asset-templates/seed -H "X-API-Key: plantos-edge-..."

# 2. List templates
curl http://127.0.0.1:8000/api/v1/asset-templates

# 3. Create binding
curl -X POST http://127.0.0.1:8000/api/v1/assets/FILTER-101/bindings \
  -H "Content-Type: application/json" \
  -H "X-API-Key: plantos-edge-..." \
  -d '{"attribute_name":"filter_dp","signal_id":"FILTER-101.filter_dp","binding_type":"direct"}'

# 4. Validate
curl -X POST http://127.0.0.1:8000/api/v1/assets/FILTER-101/bindings/validate \
  -H "X-API-Key: plantos-edge-..."

# 5. Migration on VPS
ssh plantos@103.97.132.249 "docker exec plantos-backend alembic upgrade head"

# 6. TypeScript
cd frontend && npx tsc --noEmit
```

---

## Out of Scope

- Template versioning UI (edit creates new version)
- Cross-plant template sharing
- Formula/calculation bindings (AM-4)
- KPI bindings (AM-4)
- Contract YAML export/import (future)
