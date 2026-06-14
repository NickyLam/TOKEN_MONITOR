"""Dashboard endpoints."""

from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.usage import UsageRecord
from app.models.vendor import Plan, Vendor
from app.schemas.dashboard import DailySpend, QuotaStatus, SpendOverview, UsageTrends, VendorSpendItem

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=SpendOverview)
async def get_spend_overview(db: AsyncSession = Depends(get_db)):
    """Get total spend and vendor breakdown for the current month."""
    today = date.today()
    period_start = today.replace(day=1)

    # Sum costs from usage_records for this month
    cost_stmt = (
        select(
            UsageRecord.vendor_slug,
            func.coalesce(func.sum(UsageRecord.total_cost_usd), 0).label("total_cost"),
        )
        .where(
            UsageRecord.recorded_at >= datetime.combine(period_start, datetime.min.time()),
            UsageRecord.record_type.in_(["token_usage", "cost_snapshot"]),
        )
        .group_by(UsageRecord.vendor_slug)
    )
    result = await db.execute(cost_stmt)
    vendor_costs = {row.vendor_slug: float(row.total_cost) for row in result}

    # Get subscription costs from active plans
    plan_stmt = select(Plan).options(selectinload(Plan.vendor)).where(Plan.is_active == True)
    plan_result = await db.execute(plan_stmt)
    plans = plan_result.scalars().unique().all()

    vendor_map: dict[str, VendorSpendItem] = {}
    total_spend = 0.0

    for plan in plans:
        slug = plan.vendor.slug if plan.vendor else "unknown"
        name = plan.vendor.display_name if plan.vendor else "Unknown"
        if slug not in vendor_map:
            vendor_map[slug] = VendorSpendItem(vendor_slug=slug, vendor_name=name)
        if plan.monthly_cost:
            vendor_map[slug].subscription_cost += float(plan.monthly_cost)

    for slug, cost in vendor_costs.items():
        if slug not in vendor_map:
            vendor_map[slug] = VendorSpendItem(vendor_slug=slug, vendor_name=slug)
        vendor_map[slug].spend = cost

    for item in vendor_map.values():
        total_spend += item.spend + item.subscription_cost

    return SpendOverview(
        total_spend=round(total_spend, 2),
        period_start=period_start,
        period_end=today,
        vendor_breakdown=list(vendor_map.values()),
    )


@router.get("/trends", response_model=UsageTrends)
async def get_usage_trends(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get daily spend trends over the last N days."""
    start_date = date.today() - timedelta(days=days)
    start_dt = datetime.combine(start_date, datetime.min.time())

    stmt = (
        select(
            func.date(UsageRecord.recorded_at).label("day"),
            UsageRecord.vendor_slug,
            func.coalesce(func.sum(UsageRecord.total_cost_usd), 0).label("daily_cost"),
        )
        .where(
            UsageRecord.recorded_at >= start_dt,
            UsageRecord.record_type.in_(["token_usage", "cost_snapshot"]),
        )
        .group_by("day", UsageRecord.vendor_slug)
        .order_by("day")
    )
    result = await db.execute(stmt)

    daily: dict[str, dict] = {}
    for row in result:
        day_str = str(row.day)
        if day_str not in daily:
            daily[day_str] = {"total": 0.0, "by_vendor": {}}
        cost = float(row.daily_cost)
        daily[day_str]["total"] += cost
        daily[day_str]["by_vendor"][row.vendor_slug] = cost

    daily_spend = [
        DailySpend(
            date=date.fromisoformat(day_str),
            total=round(data["total"], 4),
            by_vendor=data["by_vendor"],
        )
        for day_str, data in sorted(daily.items())
    ]

    # Simple forecast: average daily spend * remaining days in month
    today = date.today()
    days_in_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    days_in_month = days_in_month.day
    days_elapsed = today.day
    days_remaining = days_in_month - days_elapsed

    if daily_spend:
        avg_daily = sum(d.total for d in daily_spend) / len(daily_spend)
        forecast = avg_daily * days_remaining
    else:
        forecast = 0.0

    return UsageTrends(
        daily_spend=daily_spend,
        forecast_total=round(forecast, 2),
        days_projected=days_remaining,
    )


@router.get("/quota-status", response_model=list[QuotaStatus])
async def get_quota_status(db: AsyncSession = Depends(get_db)):
    """Get quota status for all active plans."""
    stmt = select(Plan).options(selectinload(Plan.vendor)).where(Plan.is_active == True)
    result = await db.execute(stmt)
    plans = result.scalars().unique().all()

    statuses: list[QuotaStatus] = []
    for plan in plans:
        vendor = plan.vendor
        slug = vendor.slug if vendor else "unknown"
        name = vendor.display_name if vendor else "Unknown"

        # Get latest quota snapshot
        quota_stmt = (
            select(UsageRecord)
            .where(UsageRecord.plan_id == plan.id, UsageRecord.record_type == "quota_snapshot")
            .order_by(UsageRecord.recorded_at.desc())
            .limit(1)
        )
        q_result = await db.execute(quota_stmt)
        latest = q_result.scalar_one_or_none()

        quota_used = latest.quota_used if latest else None
        quota_total = latest.quota_total if latest else (plan.quota_limit or None)
        quota_percent = None
        if quota_used is not None and quota_total and quota_total > 0:
            quota_percent = round((quota_used / quota_total) * 100, 1)

        days_until_renewal = None
        if plan.renewal_date:
            days_until_renewal = (plan.renewal_date - date.today()).days

        statuses.append(
            QuotaStatus(
                plan_id=plan.id,
                plan_name=plan.name,
                vendor_slug=slug,
                vendor_name=name,
                plan_type=plan.plan_type,
                quota_used=quota_used,
                quota_total=quota_total,
                quota_unit=plan.quota_unit,
                quota_percent=quota_percent,
                monthly_cost=float(plan.monthly_cost) if plan.monthly_cost else None,
                renewal_date=plan.renewal_date,
                days_until_renewal=days_until_renewal,
            )
        )

    return statuses
