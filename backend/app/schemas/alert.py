"""Alert Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ── Alert Rule ──────────────────────────────────────────

class AlertRuleCreate(BaseModel):
    plan_id: Optional[int] = None
    rule_type: str  # quota_percent | spend_dollars | plan_expiring_days | daily_spend_spike | token_threshold
    threshold_value: float
    threshold_unit: Optional[str] = None
    is_enabled: bool = True


class AlertRuleUpdate(BaseModel):
    plan_id: Optional[int] = None
    rule_type: Optional[str] = None
    threshold_value: Optional[float] = None
    threshold_unit: Optional[str] = None
    is_enabled: Optional[bool] = None


class AlertRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: Optional[int] = None
    rule_type: str
    threshold_value: float
    threshold_unit: Optional[str] = None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


# ── Alert Event ─────────────────────────────────────────

class AlertEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_rule_id: int
    plan_id: Optional[int] = None
    severity: str
    message: str
    evaluated_value: Optional[float] = None
    is_read: bool
    triggered_at: datetime
    dismissed_at: Optional[datetime] = None
