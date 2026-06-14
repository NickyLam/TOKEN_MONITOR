"""Plan CRUD endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.usage import UsageRecord
from app.models.vendor import Plan, Vendor
from app.schemas.vendor import PlanCreate, PlanDetail, PlanResponse, PlanUpdate

router = APIRouter(prefix="/api/plans", tags=["plans"])


@router.get("", response_model=list[PlanResponse])
async def list_plans(
    vendor_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Plan).options(selectinload(Plan.vendor))
    if vendor_id is not None:
        stmt = stmt.where(Plan.vendor_id == vendor_id)
    if is_active is not None:
        stmt = stmt.where(Plan.is_active == is_active)
    stmt = stmt.order_by(Plan.name)
    result = await db.execute(stmt)
    return result.scalars().unique().all()


@router.post("", response_model=PlanResponse, status_code=201)
async def create_plan(data: PlanCreate, db: AsyncSession = Depends(get_db)):
    # Verify vendor exists
    vendor = await db.get(Vendor, data.vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor id={data.vendor_id} not found")

    plan = Plan(**data.model_dump())
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return plan


@router.get("/{plan_id}", response_model=PlanDetail)
async def get_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Plan).options(selectinload(Plan.vendor)).where(Plan.id == plan_id)
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan id={plan_id} not found")

    # Get latest quota snapshot
    quota_stmt = (
        select(UsageRecord)
        .where(UsageRecord.plan_id == plan_id, UsageRecord.record_type == "quota_snapshot")
        .order_by(UsageRecord.recorded_at.desc())
        .limit(1)
    )
    quota_result = await db.execute(quota_stmt)
    latest_quota = quota_result.scalar_one_or_none()

    detail = PlanDetail.model_validate(plan)
    detail.vendor_name = plan.vendor.display_name if plan.vendor else None
    detail.vendor_slug = plan.vendor.slug if plan.vendor else None
    if latest_quota and latest_quota.quota_used is not None:
        detail.quota_used = latest_quota.quota_used
        if latest_quota.quota_total and latest_quota.quota_total > 0:
            detail.quota_percent = (latest_quota.quota_used / latest_quota.quota_total) * 100

    return detail


@router.put("/{plan_id}", response_model=PlanResponse)
async def update_plan(plan_id: int, data: PlanUpdate, db: AsyncSession = Depends(get_db)):
    plan = await db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan id={plan_id} not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)
    await db.flush()
    await db.refresh(plan)
    return plan


@router.delete("/{plan_id}", status_code=204)
async def delete_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    plan = await db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan id={plan_id} not found")
    await db.delete(plan)
    await db.flush()
