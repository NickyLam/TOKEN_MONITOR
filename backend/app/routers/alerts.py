"""Alert CRUD endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.alert import AlertEvent, AlertRule
from app.schemas.alert import (
    AlertEventResponse,
    AlertRuleCreate,
    AlertRuleResponse,
    AlertRuleUpdate,
)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


# ── Rules ───────────────────────────────────────────────


@router.get("/rules", response_model=list[AlertRuleResponse])
async def list_alert_rules(db: AsyncSession = Depends(get_db)):
    stmt = select(AlertRule).order_by(AlertRule.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/rules", response_model=AlertRuleResponse, status_code=201)
async def create_alert_rule(data: AlertRuleCreate, db: AsyncSession = Depends(get_db)):
    rule = AlertRule(**data.model_dump())
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return rule


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(rule_id: int, data: AlertRuleUpdate, db: AsyncSession = Depends(get_db)):
    rule = await db.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Alert rule id={rule_id} not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
    await db.flush()
    await db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_alert_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    rule = await db.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Alert rule id={rule_id} not found")
    await db.delete(rule)
    await db.flush()


# ── Events ──────────────────────────────────────────────


@router.get("/events", response_model=list[AlertEventResponse])
async def list_alert_events(
    is_read: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AlertEvent).order_by(AlertEvent.triggered_at.desc()).limit(limit)
    if is_read is not None:
        stmt = stmt.where(AlertEvent.is_read == is_read)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/events/{event_id}/dismiss", response_model=AlertEventResponse)
async def dismiss_alert(event_id: int, db: AsyncSession = Depends(get_db)):
    event = await db.get(AlertEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Alert event id={event_id} not found")
    event.is_read = True
    event.dismissed_at = datetime.utcnow()
    await db.flush()
    await db.refresh(event)
    return event


@router.post("/events/dismiss-all")
async def dismiss_all_alerts(db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    stmt = (
        update(AlertEvent)
        .where(AlertEvent.is_read == False)
        .values(is_read=True, dismissed_at=now)
    )
    result = await db.execute(stmt)
    await db.flush()
    return {"dismissed_count": result.rowcount}


@router.get("/events/unread-count")
async def get_unread_count(db: AsyncSession = Depends(get_db)):
    stmt = select(func.count()).select_from(AlertEvent).where(AlertEvent.is_read == False)
    result = await db.execute(stmt)
    count = result.scalar() or 0
    return {"count": count}
