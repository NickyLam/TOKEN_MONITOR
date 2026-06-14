"""Alert evaluation engine."""

import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alert import AlertEvent, AlertRule
from app.models.usage import UsageRecord
from app.models.vendor import Plan

logger = logging.getLogger(__name__)

COOLDOWN_HOURS = 4


async def evaluate_all_rules(db: AsyncSession) -> list[AlertEvent]:
    """Evaluate all enabled alert rules and create events if triggered."""
    stmt = select(AlertRule).where(AlertRule.is_enabled == True)
    result = await db.execute(stmt)
    rules = result.scalars().all()

    new_events: list[AlertEvent] = []

    for rule in rules:
        try:
            event = await _evaluate_rule(db, rule)
            if event:
                new_events.append(event)
        except Exception as e:
            logger.error("Error evaluating rule %d: %s", rule.id, e)

    return new_events


async def _evaluate_rule(db: AsyncSession, rule: AlertRule) -> AlertEvent | None:
    """Evaluate a single rule, return AlertEvent if triggered."""
    # Check cooldown
    cooldown_cutoff = datetime.utcnow() - timedelta(hours=COOLDOWN_HOURS)
    cooldown_stmt = (
        select(func.count())
        .select_from(AlertEvent)
        .where(
            AlertEvent.alert_rule_id == rule.id,
            AlertEvent.triggered_at >= cooldown_cutoff,
        )
    )
    cooldown_result = await db.execute(cooldown_stmt)
    if (cooldown_result.scalar() or 0) > 0:
        return None

    evaluated_value: float | None = None
    message = ""
    plan_id = rule.plan_id

    if rule.rule_type == "quota_percent":
        if not plan_id:
            return None
        evaluated_value, message = await _eval_quota_percent(db, plan_id)

    elif rule.rule_type == "spend_dollars":
        if not plan_id:
            return None
        evaluated_value, message = await _eval_spend_dollars(db, plan_id)

    elif rule.rule_type == "plan_expiring_days":
        if not plan_id:
            return None
        evaluated_value, message = await _eval_plan_expiring(db, plan_id)

    elif rule.rule_type == "daily_spend_spike":
        if not plan_id:
            return None
        evaluated_value, message = await _eval_daily_spike(db, plan_id)

    elif rule.rule_type == "token_threshold":
        if not plan_id:
            return None
        evaluated_value, message = await _eval_token_threshold(db, plan_id)

    else:
        return None

    if evaluated_value is None:
        return None

    # Determine if triggered
    triggered = False
    if rule.rule_type == "plan_expiring_days":
        triggered = evaluated_value <= rule.threshold_value and evaluated_value >= 0
    else:
        triggered = evaluated_value >= rule.threshold_value

    if not triggered:
        return None

    # Determine severity
    threshold = rule.threshold_value
    if rule.rule_type == "plan_expiring_days":
        if evaluated_value <= 1:
            severity = "warning"
        else:
            severity = "info"
    else:
        if evaluated_value >= threshold * 1.2:
            severity = "critical"
        elif evaluated_value >= threshold:
            severity = "warning"
        else:
            severity = "info"

    event = AlertEvent(
        alert_rule_id=rule.id,
        plan_id=plan_id,
        severity=severity,
        message=message,
        evaluated_value=evaluated_value,
    )
    db.add(event)
    await db.flush()
    return event


async def _eval_quota_percent(db: AsyncSession, plan_id: int) -> tuple[float | None, str]:
    """Evaluate quota usage percentage."""
    stmt = (
        select(UsageRecord)
        .where(UsageRecord.plan_id == plan_id, UsageRecord.record_type == "quota_snapshot")
        .order_by(UsageRecord.recorded_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    latest = result.scalar_one_or_none()
    if not latest or latest.quota_total is None or latest.quota_total == 0:
        return None, ""
    percent = (latest.quota_used / latest.quota_total) * 100
    return round(percent, 1), f"Plan quota usage at {percent:.1f}%"


async def _eval_spend_dollars(db: AsyncSession, plan_id: int) -> tuple[float | None, str]:
    """Evaluate total spend for current cycle."""
    plan = await db.get(Plan, plan_id)
    if not plan:
        return None, ""
    stmt = (
        select(func.coalesce(func.sum(UsageRecord.total_cost_usd), 0))
        .where(
            UsageRecord.plan_id == plan_id,
            UsageRecord.record_type.in_(["token_usage", "cost_snapshot"]),
        )
    )
    result = await db.execute(stmt)
    total = float(result.scalar() or 0)
    return total, f"Cycle spend: ${total:.2f}"


async def _eval_plan_expiring(db: AsyncSession, plan_id: int) -> tuple[float | None, str]:
    """Evaluate days until plan renewal."""
    plan = await db.get(Plan, plan_id)
    if not plan or not plan.renewal_date:
        return None, ""
    from datetime import date
    days = (plan.renewal_date - date.today()).days
    return float(days), f"Plan renews in {days} days"


async def _eval_daily_spike(db: AsyncSession, plan_id: int) -> tuple[float | None, str]:
    """Evaluate daily spend spike vs 14-day average."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    two_weeks_ago = today_start - timedelta(days=14)

    # Today's spend
    today_stmt = (
        select(func.coalesce(func.sum(UsageRecord.total_cost_usd), 0))
        .where(
            UsageRecord.plan_id == plan_id,
            UsageRecord.recorded_at >= today_start,
            UsageRecord.record_type.in_(["token_usage", "cost_snapshot"]),
        )
    )
    today_result = await db.execute(today_stmt)
    today_spend = float(today_result.scalar() or 0)

    # 14-day average
    avg_stmt = (
        select(func.coalesce(func.sum(UsageRecord.total_cost_usd), 0))
        .where(
            UsageRecord.plan_id == plan_id,
            UsageRecord.recorded_at >= two_weeks_ago,
            UsageRecord.recorded_at < today_start,
            UsageRecord.record_type.in_(["token_usage", "cost_snapshot"]),
        )
    )
    avg_result = await db.execute(avg_stmt)
    total_14d = float(avg_result.scalar() or 0)
    avg_daily = total_14d / 14 if total_14d > 0 else 0

    if avg_daily == 0:
        return None, ""

    ratio = today_spend / avg_daily
    return round(ratio, 2), f"Daily spend spike: {ratio:.1f}x average"


async def _eval_token_threshold(db: AsyncSession, plan_id: int) -> tuple[float | None, str]:
    """Evaluate total tokens for current cycle."""
    stmt = (
        select(
            func.coalesce(func.sum(UsageRecord.input_tokens) + func.sum(UsageRecord.output_tokens), 0)
        )
        .where(
            UsageRecord.plan_id == plan_id,
            UsageRecord.record_type == "token_usage",
        )
    )
    result = await db.execute(stmt)
    total_tokens = int(result.scalar() or 0)
    return float(total_tokens), f"Total tokens: {total_tokens:,}"
