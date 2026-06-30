"""Alarm Rule Engine — FastAPI router."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.modules.alarms.schemas import (
    AlarmRuleCreate,
    AlarmRuleUpdate,
    AlarmRuleResponse,
    AlarmEventResponse,
    CalcRuleCreate,
)
from app.modules.alarms.service import (
    AlarmRuleService,
    AlarmEvaluator,
    list_alarms,
    acknowledge_alarm,
)
from app.modules.alarms.notify import NotificationService

router = APIRouter()
rule_service = AlarmRuleService()
_notify_service = NotificationService()


class WebhookCreate(BaseModel):
    url: str


@router.post("/notifications/webhook")
def add_webhook(data: WebhookCreate):
    """Register a webhook URL for alarm notifications."""
    _notify_service.add_webhook(data.url)
    return {"status": "ok", "webhooks": len(_notify_service._webhooks)}


# ---- Alarm Rules CRUD ----

@router.post("/alarm-rules", response_model=AlarmRuleResponse, status_code=201)
def create_rule(data: AlarmRuleCreate):
    try:
        rule = rule_service.create_rule(data)
        return rule
    except ValueError as e:
        status = 409 if "already" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e))


@router.get("/alarm-rules", response_model=list[AlarmRuleResponse])
def list_rules(status: str | None = Query(None)):
    return rule_service.list_rules(status)


@router.get("/alarm-rules/{rule_id}", response_model=AlarmRuleResponse)
def get_rule(rule_id: str):
    rule = rule_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")
    return rule


@router.patch("/alarm-rules/{rule_id}", response_model=AlarmRuleResponse)
def update_rule(rule_id: str, data: AlarmRuleUpdate):
    try:
        return rule_service.update_rule(rule_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/alarm-rules/{rule_id}")
def delete_rule(rule_id: str):
    try:
        rule_service.delete_rule(rule_id)
        return {"status": "deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---- Alarm Events ----

@router.get("/alarms", response_model=list[AlarmEventResponse])
def get_alarms(
    state: str | None = Query(None),
    severity: str | None = Query(None),
    limit: int = Query(100),
):
    return list_alarms(state=state, severity=severity, limit=limit)


@router.patch("/alarms/{alarm_id}/ack", response_model=AlarmEventResponse)
def ack_alarm(alarm_id: str):
    try:
        return acknowledge_alarm(alarm_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ---- Calculated Signal Rules ----

@router.post("/calc-rules", response_model=AlarmRuleResponse, status_code=201)
def create_calc_rule(data: CalcRuleCreate):
    """Create a calculated signal rule (trigger_type='calculated')."""
    rule_data = AlarmRuleCreate(
        rule_id=data.rule_id,
        name=data.name,
        description=data.formula,
        trigger_type="calculated",
        signal_id=data.signal_id,
        condition=">",
        threshold=0,
        status="active",
    )
    try:
        return rule_service.create_rule(rule_data)
    except ValueError as e:
        status = 409 if "already" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e))


@router.get("/calc-rules", response_model=list[AlarmRuleResponse])
def list_calc_rules():
    return rule_service.list_rules(status="active")


@router.delete("/calc-rules/{rule_id}")
def delete_calc_rule(rule_id: str):
    try:
        rule_service.delete_rule(rule_id)
        return {"status": "deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))