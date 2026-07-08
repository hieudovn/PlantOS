"""Formulas — FastAPI router."""

from fastapi import APIRouter, HTTPException, Query

from app.modules.formulas.schemas import (
    CalcSignalCreate, CalcSignalUpdate, CalcSignalResponse, CalcSignalTestResult,
    KpiCreate, KpiUpdate, KpiResponse, KpiCurrentValue,
    FormulaValidateRequest, FormulaValidateResponse,
)
from app.modules.formulas.service import (
    FormulaValidationService, CalcSignalService, KpiService,
)

router = APIRouter()
validation_service = FormulaValidationService()
calc_service = CalcSignalService()
kpi_service = KpiService()


# ---- Formula Validation ----

@router.post("/formulas/validate", response_model=FormulaValidateResponse)
def validate_formula(data: FormulaValidateRequest):
    """Validate a formula expression. Optionally provide input_names for preview."""
    return validation_service.validate(data)


# ---- Calculated Signals ----

@router.post("/calculated-signals", response_model=CalcSignalResponse, status_code=201)
def create_calc_signal(data: CalcSignalCreate):
    try:
        return calc_service.create(data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/calculated-signals", response_model=list[CalcSignalResponse])
def list_calc_signals(asset_id: str | None = Query(None)):
    return calc_service.list_by_asset(asset_id)


@router.get("/calculated-signals/{calc_signal_id}", response_model=CalcSignalResponse)
def get_calc_signal(calc_signal_id: str):
    try:
        return calc_service.get(calc_signal_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/calculated-signals/{calc_signal_id}", response_model=CalcSignalResponse)
def update_calc_signal(calc_signal_id: str, data: CalcSignalUpdate):
    try:
        return calc_service.update(calc_signal_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/calculated-signals/{calc_signal_id}", status_code=204)
def delete_calc_signal(calc_signal_id: str):
    try:
        calc_service.delete(calc_signal_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/calculated-signals/{calc_signal_id}/test", response_model=CalcSignalTestResult)
def test_calc_signal(calc_signal_id: str):
    """Evaluate formula with latest values, don't save."""
    return calc_service.test(calc_signal_id)


@router.post("/calculated-signals/{calc_signal_id}/execute", response_model=CalcSignalTestResult)
def execute_calc_signal(calc_signal_id: str):
    """Evaluate formula and save results."""
    return calc_service.execute(calc_signal_id)


# ---- KPI Definitions ----

@router.post("/kpis", response_model=KpiResponse, status_code=201)
def create_kpi(data: KpiCreate):
    try:
        return kpi_service.create(data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/kpis/current/values", response_model=list[KpiCurrentValue])
def get_kpi_current_values(
    scope_type: str | None = Query(None),
    scope_id: str | None = Query(None),
):
    """Evaluate all KPIs matching scope, return current values."""
    return kpi_service.get_current_values(scope_type=scope_type, scope_id=scope_id)


@router.get("/kpis", response_model=list[KpiResponse])
def list_kpis(
    scope_type: str | None = Query(None),
    scope_id: str | None = Query(None),
):
    return kpi_service.list_all(scope_type=scope_type, scope_id=scope_id)


@router.get("/kpis/{kpi_id}", response_model=KpiResponse)
def get_kpi(kpi_id: str):
    try:
        return kpi_service.get(kpi_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/kpis/{kpi_id}", response_model=KpiResponse)
def update_kpi(kpi_id: str, data: KpiUpdate):
    try:
        return kpi_service.update(kpi_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/kpis/{kpi_id}", status_code=204)
def delete_kpi(kpi_id: str):
    try:
        kpi_service.delete(kpi_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/kpis/{kpi_id}/test", response_model=CalcSignalTestResult)
def test_kpi(kpi_id: str):
    """Evaluate KPI formula with latest values."""
    return kpi_service.test(kpi_id)
