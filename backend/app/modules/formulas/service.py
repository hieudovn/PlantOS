"""Formulas — Service layer."""

import json
import logging
from sqlalchemy import select, and_

from app.db import get_session
from app.modules.formulas.models import CalculatedSignal, KpiDefinition
from app.modules.formulas.schemas import (
    CalcSignalCreate, CalcSignalUpdate, CalcSignalResponse,
    CalcSignalTestResult,
    KpiCreate, KpiUpdate, KpiResponse, KpiCurrentValue,
    FormulaValidateRequest, FormulaValidateResponse,
)
from datetime import datetime, timezone
from app.modules.signals.models import Signal
from app.modules.formulas.engine import SafeFormulaEngine, FormulaError

logger = logging.getLogger(__name__)
engine = SafeFormulaEngine()


# ---- Helpers ----

def _calc_to_response(c: CalculatedSignal) -> CalcSignalResponse:
    inputs = c.inputs_json if isinstance(c.inputs_json, list) else []
    return CalcSignalResponse(
        calc_signal_id=c.calc_signal_id,
        asset_id=c.asset_id,
        name=c.name,
        display_name=c.display_name,
        formula=c.formula,
        inputs=inputs,
        output_signal_id=c.output_signal_id,
        output_unit=c.output_unit,
        execution_mode=c.execution_mode,
        status=c.status,
        version=c.version,
        last_run_at=c.last_run_at,
        last_run_status=c.last_run_status,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


def _kpi_to_response(k: KpiDefinition) -> KpiResponse:
    inputs = k.inputs_json if isinstance(k.inputs_json, list) else []
    return KpiResponse(
        kpi_id=k.kpi_id,
        scope_type=k.scope_type,
        scope_id=k.scope_id,
        name=k.name,
        display_name=k.display_name,
        description=k.description,
        kpi_category=k.kpi_category,
        formula=k.formula,
        inputs=inputs,
        unit=k.unit,
        aggregation_window=k.aggregation_window,
        target=k.target,
        warning_limit=k.warning_limit,
        critical_limit=k.critical_limit,
        display_priority=k.display_priority,
        show_in_process_view=k.show_in_process_view,
        status=k.status,
        version=k.version,
        created_at=k.created_at,
        updated_at=k.updated_at,
    )


def _resolve_inputs(inputs: list[dict], session) -> dict[str, float]:
    """Resolve input variable names to current values."""
    from app.modules.measurements.service import MeasurementService
    resolved = {}
    for inp in inputs:
        var = inp.get("variable_name", "")
        sig_id = inp.get("signal_id", "")
        if not var or not sig_id:
            continue
        # Query current value
        try:
            ms = MeasurementService()
            cv = ms.get_current_values(signal_ids=[sig_id])
            if cv and len(cv) > 0:
                resolved[var] = float(cv[0].value)
            else:
                resolved[var] = 0.0
        except Exception as ex:
            logger.warning(f"Could not resolve signal '{sig_id}': {ex}")
            resolved[var] = 0.0
    return resolved


# ---- Validation Service ----

class FormulaValidationService:
    def validate(self, req: FormulaValidateRequest) -> FormulaValidateResponse:
        """Validate formula and optionally compute preview."""
        errors = engine.validate(req.formula, req.input_names)
        preview = None
        if not errors and req.input_names:
            try:
                dummy_inputs = {name: 0.0 for name in req.input_names}
                preview = engine.evaluate(req.formula, dummy_inputs)
            except FormulaError:
                pass
        return FormulaValidateResponse(
            valid=len(errors) == 0,
            errors=errors,
            preview_value=preview,
        )


# ---- Calculated Signal Service ----

class CalcSignalService:
    def create(self, data: CalcSignalCreate) -> CalcSignalResponse:
        with get_session() as session:
            existing = session.get(CalculatedSignal, data.calc_signal_id)
            if existing:
                raise ValueError(f"Calculated signal '{data.calc_signal_id}' already exists")
            cs = CalculatedSignal(
                calc_signal_id=data.calc_signal_id,
                asset_id=data.asset_id,
                name=data.name,
                display_name=data.display_name,
                formula=data.formula,
                formula_meta_json={},
                inputs_json=[i.model_dump() for i in data.inputs],
                output_signal_id=data.output_signal_id,
                output_unit=data.output_unit,
                execution_mode=data.execution_mode,
                status=data.status,
            )
            session.add(cs)
            session.commit()
            session.refresh(cs)
            return _calc_to_response(cs)

    def get(self, calc_signal_id: str) -> CalcSignalResponse:
        with get_session() as session:
            cs = session.get(CalculatedSignal, calc_signal_id)
            if not cs:
                raise ValueError(f"Calculated signal '{calc_signal_id}' not found")
            return _calc_to_response(cs)

    def list_by_asset(self, asset_id: str | None = None) -> list[CalcSignalResponse]:
        with get_session() as session:
            stmt = select(CalculatedSignal).order_by(CalculatedSignal.name)
            if asset_id:
                stmt = stmt.where(CalculatedSignal.asset_id == asset_id)
            results = session.scalars(stmt).all()
            return [_calc_to_response(c) for c in results]

    def update(self, calc_signal_id: str, data: CalcSignalUpdate) -> CalcSignalResponse:
        with get_session() as session:
            cs = session.get(CalculatedSignal, calc_signal_id)
            if not cs:
                raise ValueError(f"Calculated signal '{calc_signal_id}' not found")
            update_data = data.model_dump(exclude_unset=True)
            if "inputs" in update_data:
                update_data["inputs_json"] = [i.model_dump() for i in update_data.pop("inputs")]
            for key, value in update_data.items():
                if value is not None:
                    setattr(cs, key, value)
            session.commit()
            session.refresh(cs)
            return _calc_to_response(cs)

    def delete(self, calc_signal_id: str) -> None:
        with get_session() as session:
            cs = session.get(CalculatedSignal, calc_signal_id)
            if not cs:
                raise ValueError(f"Calculated signal '{calc_signal_id}' not found")
            session.delete(cs)
            session.commit()

    def test(self, calc_signal_id: str) -> CalcSignalTestResult:
        """Evaluate formula with latest values, don't save."""
        with get_session() as session:
            cs = session.get(CalculatedSignal, calc_signal_id)
            if not cs:
                return CalcSignalTestResult(status="error", error="Not found")
            inputs = cs.inputs_json if isinstance(cs.inputs_json, list) else []
            resolved = _resolve_inputs(inputs, session)
            try:
                result = engine.evaluate(cs.formula, resolved)
                return CalcSignalTestResult(status="ok", result=result, inputs=resolved)
            except FormulaError as e:
                return CalcSignalTestResult(status="error", error=str(e), inputs=resolved)

    def execute(self, calc_signal_id: str) -> CalcSignalTestResult:
        """Evaluate formula and save results."""
        with get_session() as session:
            cs = session.get(CalculatedSignal, calc_signal_id)
            if not cs:
                return CalcSignalTestResult(status="error", error="Not found")
            inputs = cs.inputs_json if isinstance(cs.inputs_json, list) else []
            resolved = _resolve_inputs(inputs, session)
            try:
                result = engine.evaluate(cs.formula, resolved)
                cs.last_run_at = datetime.now(timezone.utc)
                cs.last_run_status = "ok"
                session.commit()
                return CalcSignalTestResult(status="ok", result=result, inputs=resolved)
            except FormulaError as e:
                cs.last_run_at = datetime.now(timezone.utc)
                cs.last_run_status = "error"
                session.commit()
                return CalcSignalTestResult(status="error", error=str(e), inputs=resolved)


# ---- KPI Service ----

class KpiService:
    def create(self, data: KpiCreate) -> KpiResponse:
        with get_session() as session:
            existing = session.get(KpiDefinition, data.kpi_id)
            if existing:
                raise ValueError(f"KPI '{data.kpi_id}' already exists")
            kpi = KpiDefinition(
                kpi_id=data.kpi_id,
                scope_type=data.scope_type,
                scope_id=data.scope_id,
                name=data.name,
                display_name=data.display_name,
                description=data.description,
                kpi_category=data.kpi_category,
                formula=data.formula,
                formula_meta_json={},
                inputs_json=[i.model_dump() for i in data.inputs],
                unit=data.unit,
                aggregation_window=data.aggregation_window,
                target=data.target,
                warning_limit=data.warning_limit,
                critical_limit=data.critical_limit,
                display_priority=data.display_priority,
                show_in_process_view=data.show_in_process_view,
                status=data.status,
            )
            session.add(kpi)
            session.commit()
            session.refresh(kpi)
            return _kpi_to_response(kpi)

    def get(self, kpi_id: str) -> KpiResponse:
        with get_session() as session:
            kpi = session.get(KpiDefinition, kpi_id)
            if not kpi:
                raise ValueError(f"KPI '{kpi_id}' not found")
            return _kpi_to_response(kpi)

    def list_all(self, scope_type: str | None = None, scope_id: str | None = None) -> list[KpiResponse]:
        with get_session() as session:
            stmt = select(KpiDefinition).order_by(KpiDefinition.display_priority.desc(), KpiDefinition.name)
            if scope_type:
                stmt = stmt.where(KpiDefinition.scope_type == scope_type)
            if scope_id:
                stmt = stmt.where(KpiDefinition.scope_id == scope_id)
            results = session.scalars(stmt).all()
            return [_kpi_to_response(k) for k in results]

    def update(self, kpi_id: str, data: KpiUpdate) -> KpiResponse:
        with get_session() as session:
            kpi = session.get(KpiDefinition, kpi_id)
            if not kpi:
                raise ValueError(f"KPI '{kpi_id}' not found")
            update_data = data.model_dump(exclude_unset=True)
            if "inputs" in update_data:
                update_data["inputs_json"] = [i.model_dump() for i in update_data.pop("inputs")]
            for key, value in update_data.items():
                if value is not None:
                    setattr(kpi, key, value)
            session.commit()
            session.refresh(kpi)
            return _kpi_to_response(kpi)

    def delete(self, kpi_id: str) -> None:
        with get_session() as session:
            kpi = session.get(KpiDefinition, kpi_id)
            if not kpi:
                raise ValueError(f"KPI '{kpi_id}' not found")
            session.delete(kpi)
            session.commit()

    def test(self, kpi_id: str) -> CalcSignalTestResult:
        """Evaluate KPI formula with latest values."""
        with get_session() as session:
            kpi = session.get(KpiDefinition, kpi_id)
            if not kpi:
                return CalcSignalTestResult(status="error", error="Not found")
            inputs = kpi.inputs_json if isinstance(kpi.inputs_json, list) else []
            resolved = _resolve_inputs(inputs, session)
            try:
                result = engine.evaluate(kpi.formula, resolved)
                return CalcSignalTestResult(status="ok", result=result, inputs=resolved)
            except FormulaError as e:
                return CalcSignalTestResult(status="error", error=str(e), inputs=resolved)

    def get_current_values(self, scope_type: str | None = None, scope_id: str | None = None) -> list[KpiCurrentValue]:
        """Evaluate all KPIs matching scope, return current values."""
        kpis = self.list_all(scope_type=scope_type, scope_id=scope_id)
        results = []
        for kpi in kpis:
            test_result = self.test(kpi.kpi_id)
            status = "unknown"
            if test_result.result is not None:
                if kpi.critical_limit is not None and test_result.result >= kpi.critical_limit:
                    status = "critical"
                elif kpi.warning_limit is not None and test_result.result >= kpi.warning_limit:
                    status = "warning"
                else:
                    status = "good"
            results.append(KpiCurrentValue(
                kpi_id=kpi.kpi_id,
                name=kpi.name,
                display_name=kpi.display_name,
                value=test_result.result,
                unit=kpi.unit,
                target=kpi.target,
                warning_limit=kpi.warning_limit,
                critical_limit=kpi.critical_limit,
                status=status if test_result.status == "ok" else "error",
            ))
        return results
