# Phase AM-4 — Formula/KPI Editor

> **Phase:** AM-4 (Asset Model Builder)  
> **Depends on:** AM-3 (templates + bindings ready)  
> **Effort:** 3-4h  
> **Critical SA Requirement:** AST-based safe expression evaluator. NO raw `eval()`.

---

## Objective

Create a safe formula engine for calculated signals and KPIs. SA mandates an AST-based approach — parse the formula, validate allowed nodes, execute against latest signal values. No arbitrary code execution.

---

## Task 1: Safe Formula Engine

**New file:** `backend/app/modules/formulas/engine.py`

```python
"""AST-based safe expression evaluator for PlantOS formulas.

Allowed:
- Numeric literals (int, float)
- Variable names (resolved from signal inputs)
- Binary operators: + - * / ** %
- Unary operators: + -
- Comparison: > >= < <= == !=
- Boolean: and or not
- Function calls from registered whitelist
- Ternary: x if cond else y  (or if(cond, x, y))

Forbidden:
- Attribute access, subscript, lambda, comprehension
- Assignment, loop, class/function definition
- __import__, __builtins__, eval, exec
- File/network/db access
"""

import ast
import operator
import math
from typing import Any


class FormulaError(Exception):
    """Raised when formula is invalid or execution fails."""
    pass


class SafeFormulaEngine:
    """AST-based safe expression evaluator."""

    # Allowed built-in functions (whitelist)
    ALLOWED_FUNCTIONS = {
        # Math
        'abs': abs, 'round': round,
        'min': min, 'max': max, 'sum': sum,
        # Domain-specific
        'clamp': lambda x, lo, hi: max(lo, min(x, hi)),
        'normalize': lambda x, lo, hi: (x - lo) / (hi - lo) if hi != lo else 0,
        'if': lambda cond, a, b: a if cond else b,
    }

    # Allowed operators
    ALLOWED_OPS = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.USub: operator.neg, ast.UAdd: operator.pos,
        ast.Eq: operator.eq, ast.NotEq: operator.ne,
        ast.Lt: operator.lt, ast.LtE: operator.le,
        ast.Gt: operator.gt, ast.GtE: operator.ge,
    }

    def validate(self, formula: str, input_names: list[str]) -> list[str]:
        """Parse formula and return list of validation errors (empty = valid)."""
        errors = []
        try:
            tree = ast.parse(formula.strip(), mode='eval')
        except SyntaxError as e:
            return [f"Syntax error: {e.msg}"]
        
        visitor = _ValidatorVisitor(input_names, self.ALLOWED_FUNCTIONS)
        visitor.visit(tree)
        return visitor.errors

    def evaluate(self, formula: str, inputs: dict[str, float]) -> float:
        """Execute formula against input values. Raises FormulaError on failure."""
        try:
            tree = ast.parse(formula.strip(), mode='eval')
        except SyntaxError as e:
            raise FormulaError(f"Syntax error: {e.msg}")

        evaluator = _EvaluatorVisitor(inputs, self.ALLOWED_FUNCTIONS, self.ALLOWED_OPS)
        result = evaluator.visit(tree.body)
        if result is None:
            raise FormulaError("Formula returned None")
        return float(result)


class _ValidatorVisitor(ast.NodeVisitor):
    """Walk AST and collect all violations."""

    def __init__(self, input_names: list[str], allowed_funcs: dict):
        self.input_names = set(input_names)
        self.allowed_funcs = set(allowed_funcs)
        self.errors: list[str] = []

    def visit_Name(self, node: ast.Name):
        if node.id not in self.input_names and node.id not in self.allowed_funcs:
            self.errors.append(f"Unknown variable or function: '{node.id}'")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id not in self.allowed_funcs:
                self.errors.append(f"Forbidden function: '{node.func.id}'")
        else:
            self.errors.append("Only simple function calls are allowed (e.g. clamp(A, 0, 100))")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        self.errors.append(f"Forbidden: attribute access (e.g. {ast.unparse(node)})")
        # Don't visit children — stop here

    def visit_Subscript(self, node: ast.Subscript):
        self.errors.append("Forbidden: subscript/slice access")
        # Don't visit children

    def visit_Lambda(self, node: ast.Lambda):
        self.errors.append("Forbidden: lambda expressions")

    def visit_ListComp(self, node: ast.ListComp):
        self.errors.append("Forbidden: list comprehensions")


class _EvaluatorVisitor(ast.NodeVisitor):
    """Walk AST and compute result."""

    def __init__(self, inputs: dict[str, float], allowed_funcs: dict, allowed_ops: dict):
        self.inputs = inputs
        self.funcs = allowed_funcs
        self.ops = allowed_ops

    def visit_Expression(self, node: ast.Expression):
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise FormulaError(f"Unsupported constant type: {type(node.value)}")

    def visit_Name(self, node: ast.Name):
        if node.id in self.inputs:
            return float(self.inputs[node.id])
        if node.id in self.funcs:
            return self.funcs[node.id]  # Return callable, used in visit_Call
        raise FormulaError(f"Unknown variable: '{node.id}'")

    def visit_UnaryOp(self, node: ast.UnaryOp):
        operand = self.visit(node.operand)
        op_func = self.ops.get(type(node.op))
        if op_func is None:
            raise FormulaError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op_func(operand)

    def visit_BinOp(self, node: ast.BinOp):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_func = self.ops.get(type(node.op))
        if op_func is None:
            raise FormulaError(f"Unsupported operator: {type(node.op).__name__}")
        return op_func(left, right)

    def visit_BoolOp(self, node: ast.BoolOp):
        values = [self.visit(v) for v in node.values]
        if isinstance(node.op, ast.And):
            return float(all(values))
        elif isinstance(node.op, ast.Or):
            return float(any(values))
        raise FormulaError(f"Unsupported boolean operator")

    def visit_Compare(self, node: ast.Compare):
        left = self.visit(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            op_func = self.ops.get(type(op))
            if op_func is None:
                raise FormulaError(f"Unsupported comparison: {type(op).__name__}")
            if not op_func(left, right):
                return 0.0
        return 1.0

    def visit_IfExp(self, node: ast.IfExp):
        cond = self.visit(node.test)
        if cond:
            return self.visit(node.body)
        return self.visit(node.orelse)

    def visit_Call(self, node: ast.Call):
        func = self.visit(node.func)
        if not callable(func):
            raise FormulaError(f"'{ast.unparse(node.func)}' is not callable")
        args = [self.visit(a) for a in node.args]
        try:
            return float(func(*args))
        except Exception as e:
            raise FormulaError(f"Function call error: {e}")

    def generic_visit(self, node):
        raise FormulaError(f"Unsupported expression: {type(node).__name__}")
```

### Unit tests

**File:** `backend/tests/test_formula_engine.py`

```python
import pytest
from app.modules.formulas.engine import SafeFormulaEngine, FormulaError


def test_simple_arithmetic():
    e = SafeFormulaEngine()
    assert e.evaluate("2 + 3 * 4", {}) == 14
    assert e.evaluate("A + B", {"A": 5, "B": 3}) == 8

def test_builtin_functions():
    e = SafeFormulaEngine()
    assert e.evaluate("abs(-5)", {}) == 5
    assert e.evaluate("clamp(A, 0, 100)", {"A": 150}) == 100
    assert e.evaluate("normalize(50, 0, 100)", {}) == 0.5

def test_if_expression():
    e = SafeFormulaEngine()
    assert e.evaluate("if(A > 10, 1, 0)", {"A": 15}) == 1
    assert e.evaluate("if(A > 10, 1, 0)", {"A": 5}) == 0

def test_validation_errors():
    e = SafeFormulaEngine()
    errors = e.validate("__import__('os')", [])
    assert len(errors) > 0
    errors = e.validate("A.x", ["A"])
    assert len(errors) > 0
    errors = e.validate("lambda x: x", [])
    assert len(errors) > 0

def test_unknown_variable():
    e = SafeFormulaEngine()
    errors = e.validate("X + Y", ["A"])
    assert len(errors) == 2

def test_syntax_error():
    e = SafeFormulaEngine()
    errors = e.validate("2 +", [])
    assert len(errors) > 0

def test_division_by_zero():
    e = SafeFormulaEngine()
    with pytest.raises(FormulaError):
        e.evaluate("1 / 0", {})

def test_empty_formula():
    e = SafeFormulaEngine()
    errors = e.validate("", [])
    assert len(errors) > 0

def test_wtp_realistic():
    """Test a realistic WTP formula: filter clogging index."""
    e = SafeFormulaEngine()
    formula = "normalize(DP, 0, 100) * 0.7 + normalize(TB, 0, 2) * 0.3"
    assert e.validate(formula, ["DP", "TB"]) == []
    result = e.evaluate(formula, {"DP": 45, "TB": 0.5})
    assert 0 <= result <= 1
```

---

## Task 2: Migration 007 — Calculated Signals

**File:** `backend/migrations/versions/007_calculated_signals.py`

```sql
CREATE TABLE calculated_signals (
    calc_signal_id VARCHAR(128) PRIMARY KEY,
    asset_id VARCHAR(128) NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    name VARCHAR(128) NOT NULL,
    display_name VARCHAR(255),
    formula TEXT NOT NULL,
    formula_meta_json JSONB DEFAULT '{}',
    inputs_json JSONB NOT NULL DEFAULT '[]',
    output_signal_id VARCHAR(256),
    output_unit VARCHAR(64),
    execution_mode VARCHAR(32) DEFAULT 'manual',
    schedule_interval INTEGER,
    status VARCHAR(32) DEFAULT 'draft',
    version INTEGER DEFAULT 1,
    last_run_at TIMESTAMPTZ,
    last_run_status VARCHAR(32),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Also create `migrate_007.py` at repo root for VPS deployment.

---

## Task 3: Migration 008 — KPI Definitions

**File:** `backend/migrations/versions/008_kpi_definitions.py`

```sql
CREATE TABLE kpi_definitions (
    kpi_id VARCHAR(128) PRIMARY KEY,
    scope_type VARCHAR(32) NOT NULL,
    scope_id VARCHAR(128) NOT NULL,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    kpi_category VARCHAR(32) DEFAULT 'operation',
    formula TEXT NOT NULL,
    formula_meta_json JSONB DEFAULT '{}',
    inputs_json JSONB NOT NULL DEFAULT '[]',
    unit VARCHAR(64),
    aggregation_window VARCHAR(32),
    target NUMERIC,
    warning_limit NUMERIC,
    critical_limit NUMERIC,
    display_priority INTEGER DEFAULT 0,
    show_in_process_view BOOLEAN DEFAULT false,
    status VARCHAR(32) DEFAULT 'draft',
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## Task 4: ORM Models + API

**New files in `backend/app/modules/formulas/`:**

- `models.py` — `CalculatedSignal`, `KpiDefinition` ORM classes
- `schemas.py` — Pydantic schemas for CRUD
- `service.py` — CRUD + execute + test logic
- `router.py` — API endpoints

### API Endpoints:

```
POST   /api/v1/calculated-signals                  Create
GET    /api/v1/calculated-signals                  List (filter: asset_id)
GET    /api/v1/calculated-signals/{id}              Get
PATCH  /api/v1/calculated-signals/{id}              Update
DELETE /api/v1/calculated-signals/{id}              Delete
POST   /api/v1/calculated-signals/{id}/test         Test with latest values
POST   /api/v1/calculated-signals/{id}/execute      Run now (save result)

POST   /api/v1/kpis                                Create
GET    /api/v1/kpis                                List (filter: scope_type, scope_id)
GET    /api/v1/kpis/{id}                            Get
PATCH  /api/v1/kpis/{id}                            Update
DELETE /api/v1/kpis/{id}                            Delete
POST   /api/v1/kpis/{id}/test                       Test with latest values
GET    /api/v1/kpis/current                         Current values (filter: scope)

POST   /api/v1/formulas/validate                    Validate formula
Body:  { "formula": "A + B", "input_names": ["A", "B"] }
Resp:  { "valid": true/false, "errors": [...], "preview_value": 42.5 }
```

### Test endpoint implementation:

`POST /api/v1/calculated-signals/{id}/test`:
1. Load formula and inputs_json
2. For each input signal_id, query `GET /api/v1/measurements/current?signal_id=X`
3. Build inputs dict
4. Call `engine.evaluate(formula, inputs)`
5. Return `{ "result": 42.5, "inputs": {...}, "status": "ok" }`

### Execute endpoint:

`POST /api/v1/calculated-signals/{id}/execute`:
1. Calculate result (same as test)
2. Save result to a new signal row (or update existing)
3. Update `last_run_at`, `last_run_status`

Register router in `v1.py`:
```python
from app.modules.formulas.router import router as formulas_router
router.include_router(formulas_router, tags=["Formulas"])
```

---

## Task 5: Frontend — Formula Editor

**New file:** `frontend/src/features/formulas/FormulaEditor.tsx`

### Features:
- TextArea for formula input
- "Inputs" section: search + select signals, assign to variable names (A, B, C...)
- "Test" button → calls `POST /api/v1/formulas/validate`
- Shows preview value + any errors
- Save button for create/update

### UI Layout:
```
┌─────────────────────────────────────────┐
│ Formula Editor                           │
├─────────────────────────────────────────┤
│ Inputs:                                  │
│  A = [HSP-101.flow_rate          ▼] [+] │
│  B = [FILTER-101.filter_dp       ▼] [+] │
│                                          │
│ Formula:                                 │
│ ┌─────────────────────────────────────┐  │
│ │ A * 0.5 + normalize(B, 0, 100)     │  │
│ └─────────────────────────────────────┘  │
│                                          │
│ [Test]  Result: 523.4  ✅ Valid          │
│                                          │
│ Output Signal: [HSP-101.combined_idx  ]  │
│ Unit: [m3/h]                             │
│                                          │
│ [Save Draft]  [Activate]                 │
└─────────────────────────────────────────┘
```

---

## Task 6: Frontend — Calculated Signals Page

**New file:** `frontend/src/features/formulas/CalculatedSignalsPage.tsx`

- List calculated signals per asset
- Create/Edit/Delete with FormulaEditor
- Execute/Test buttons per row
- Status badges (draft, active, error)

### Route:
Add to `frontend/src/routes/index.tsx`:
```tsx
{ path: "formulas", element: <CalculatedSignalsPage /> },
{ path: "kpis", element: <KpiDefinitionsPage /> },
```

Sidebar links (optional — can wait for AM-5).

---

## Task 7: Frontend — KPI Definitions Page

**New file:** `frontend/src/features/formulas/KpiDefinitionsPage.tsx`

- List KPIs by scope (plant/area/asset)
- Create/Edit with FormulaEditor + thresholds
- Show current values

---

## Validation

```bash
# 1. Formula engine tests
cd backend && python -m pytest tests/test_formula_engine.py -v

# 2. Validate API
curl -X POST http://127.0.0.1:8000/api/v1/formulas/validate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ..." \
  -d '{"formula":"A + B * 2","input_names":["A","B"]}'
# → {"valid":true,"errors":[],"preview_value":null}

# 3. Security check: must reject
curl ... -d '{"formula":"__import__(\"os\").system(\"ls\")","input_names":[]}'
# → {"valid":false,"errors":["Forbidden function: '__import__'"]}

# 4. Migration
ssh plantos@103.97.132.249 "docker cp migrate_007.py plantos-backend:/app/ && docker exec plantos-backend python /app/migrate_007.py"

# 5. TypeScript
cd frontend && npx tsc --noEmit
```

---

## Out of Scope

- Scheduled execution (APScheduler)
- Historian write for calculated signals
- Visual rule chain editor
- KPI aggregation periods (time-windowed)
- Plant-level KPI dashboard
