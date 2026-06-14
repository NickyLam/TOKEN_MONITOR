"""Background polling jobs."""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.polling import PollingConfig
from app.models.usage import UsageRecord
from app.models.vendor import Plan

logger = logging.getLogger(__name__)


async def poll_vendor(vendor_slug: str):
    """Scheduled job: poll all active plans for a vendor."""
    async with async_session_factory() as session:
        await poll_vendor_plans(vendor_slug, session)
        await session.commit()


async def poll_vendor_plans(vendor_slug: str, db: AsyncSession) -> dict:
    """Poll all active plans for a vendor and insert usage records."""
    from app.plugins.registry import get_plugin

    plugin = get_plugin(vendor_slug)
    if not plugin:
        return {"success": False, "error": f"Plugin '{vendor_slug}' not found"}

    # Load active plans for this vendor
    from app.models.vendor import Vendor
    vendor_stmt = select(Vendor).where(Vendor.slug == vendor_slug)
    vendor_result = await db.execute(vendor_stmt)
    vendor = vendor_result.scalar_one_or_none()

    if not vendor:
        return {"success": False, "error": f"Vendor '{vendor_slug}' not found in DB"}

    plan_stmt = select(Plan).where(Plan.vendor_id == vendor.id, Plan.is_active == True)
    plan_result = await db.execute(plan_stmt)
    plans = plan_result.scalars().all()

    records_inserted = 0
    errors = []

    for plan in plans:
        plan_config = {
            "api_key": plan.api_key_ref or "",
            "extra_config": plan.extra_config or {},
            "plan_type": plan.plan_type,
        }

        try:
            poll_result = await plugin.poll(plan_config)

            # Insert quota snapshot
            if poll_result.quota:
                record = UsageRecord(
                    plan_id=plan.id,
                    vendor_slug=vendor_slug,
                    record_type="quota_snapshot",
                    quota_used=poll_result.quota.used,
                    quota_total=poll_result.quota.total,
                    period_start=poll_result.quota.period_start,
                    period_end=poll_result.quota.period_end,
                    raw_response=poll_result.raw_response,
                )
                db.add(record)
                records_inserted += 1

            # Insert token usage entries
            for entry in poll_result.token_entries:
                record = UsageRecord(
                    plan_id=plan.id,
                    vendor_slug=vendor_slug,
                    record_type="token_usage",
                    input_tokens=entry.input_tokens,
                    output_tokens=entry.output_tokens,
                    cache_read_tokens=entry.cache_read_tokens,
                    cache_write_tokens=entry.cache_write_tokens,
                    total_cost_usd=entry.cost_usd,
                    request_count=entry.request_count,
                    model_name=entry.model,
                )
                db.add(record)
                records_inserted += 1

            # Insert cost snapshot
            if poll_result.total_cost_usd is not None:
                record = UsageRecord(
                    plan_id=plan.id,
                    vendor_slug=vendor_slug,
                    record_type="cost_snapshot",
                    total_cost_usd=poll_result.total_cost_usd,
                    raw_response=poll_result.raw_response,
                )
                db.add(record)
                records_inserted += 1

        except Exception as e:
            logger.error("Error polling plan %s (vendor=%s): %s", plan.id, vendor_slug, e)
            errors.append(str(e))

    # Update polling config
    config_stmt = select(PollingConfig).where(PollingConfig.vendor_slug == vendor_slug)
    config_result = await db.execute(config_stmt)
    config = config_result.scalar_one_or_none()
    if config:
        config.last_polled_at = datetime.utcnow()
        if errors:
            config.last_error = "; ".join(errors)
            config.consecutive_failures += 1
        else:
            config.last_success_at = datetime.utcnow()
            config.consecutive_failures = 0

    await db.flush()

    return {
        "success": len(errors) == 0,
        "records_inserted": records_inserted,
        "plans_polled": len(plans),
        "errors": errors if errors else None,
    }


async def evaluate_alerts_job():
    """Scheduled job: evaluate all alert rules."""
    async with async_session_factory() as session:
        from app.services.alert_service import evaluate_all_rules
        await evaluate_all_rules(session)
        await session.commit()
