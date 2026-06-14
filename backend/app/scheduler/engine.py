"""APScheduler setup and lifecycle management."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


async def init_scheduler():
    """Start the scheduler and register jobs from polling configs."""
    from app.database import async_session_factory
    from app.models.polling import PollingConfig
    from app.scheduler.jobs import evaluate_alerts_job, poll_vendor

    from sqlalchemy import select

    async with async_session_factory() as session:
        stmt = select(PollingConfig).where(PollingConfig.is_enabled == True)
        result = await session.execute(stmt)
        configs = result.scalars().all()

        for config in configs:
            _add_poll_job(config.vendor_slug, config.interval_minutes)

    # Alert evaluation job every 15 minutes
    scheduler.add_job(
        func=evaluate_alerts_job,
        trigger=IntervalTrigger(minutes=15),
        id="evaluate_alerts",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    scheduler.start()
    logger.info("Scheduler started with %d poll jobs + alert evaluation", len(configs))


def _add_poll_job(vendor_slug: str, interval_minutes: int):
    """Add or replace a poll job for a vendor."""
    from app.scheduler.jobs import poll_vendor

    scheduler.add_job(
        func=poll_vendor,
        trigger=IntervalTrigger(minutes=interval_minutes),
        args=[vendor_slug],
        id=f"poll_{vendor_slug}",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )


async def shutdown_scheduler():
    """Gracefully shut down the scheduler."""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler shut down")
