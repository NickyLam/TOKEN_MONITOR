"""Polling management endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.polling import PollingConfig
from app.models.vendor import Vendor
from app.schemas.polling import PollingConfigResponse, PollingConfigUpdate, PollingStatus

router = APIRouter(prefix="/api/polling", tags=["polling"])


@router.get("/status", response_model=list[PollingStatus])
async def get_polling_status(db: AsyncSession = Depends(get_db)):
    stmt = select(PollingConfig).order_by(PollingConfig.vendor_slug)
    result = await db.execute(stmt)
    configs = result.scalars().all()

    # Get vendor display names
    vendor_stmt = select(Vendor)
    vendor_result = await db.execute(vendor_stmt)
    vendor_map = {v.slug: v.display_name for v in vendor_result.scalars().all()}

    return [
        PollingStatus(
            vendor_slug=c.vendor_slug,
            is_enabled=c.is_enabled,
            interval_minutes=c.interval_minutes,
            last_polled_at=c.last_polled_at,
            last_success_at=c.last_success_at,
            last_error=c.last_error,
            consecutive_failures=c.consecutive_failures,
            display_name=vendor_map.get(c.vendor_slug, c.vendor_slug),
        )
        for c in configs
    ]


@router.post("/trigger/{vendor_slug}")
async def trigger_poll(vendor_slug: str, db: AsyncSession = Depends(get_db)):
    """Manually trigger a poll for a vendor."""
    from app.plugins.registry import get_plugin
    from app.scheduler.jobs import poll_vendor_plans

    plugin = get_plugin(vendor_slug)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin for '{vendor_slug}' not found")

    result = await poll_vendor_plans(vendor_slug, db)
    return result


@router.put("/config/{vendor_slug}", response_model=PollingConfigResponse)
async def update_polling_config(
    vendor_slug: str,
    data: PollingConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PollingConfig).where(PollingConfig.vendor_slug == vendor_slug)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail=f"Polling config for '{vendor_slug}' not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
    await db.flush()
    await db.refresh(config)
    return config
