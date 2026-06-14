"""Vendor CRUD endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.vendor import Plan, Vendor
from app.schemas.vendor import VendorCreate, VendorDetail, VendorResponse, VendorUpdate

router = APIRouter(prefix="/api/vendors", tags=["vendors"])


@router.get("", response_model=list[VendorResponse])
async def list_vendors(
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Vendor)
    if is_active is not None:
        stmt = stmt.where(Vendor.is_active == is_active)
    stmt = stmt.order_by(Vendor.display_name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=VendorResponse, status_code=201)
async def create_vendor(data: VendorCreate, db: AsyncSession = Depends(get_db)):
    vendor = Vendor(**data.model_dump())
    db.add(vendor)
    await db.flush()
    await db.refresh(vendor)
    return vendor


@router.get("/{slug}", response_model=VendorDetail)
async def get_vendor(slug: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Vendor).where(Vendor.slug == slug)
    result = await db.execute(stmt)
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor '{slug}' not found")

    count_stmt = select(func.count()).select_from(Plan).where(Plan.vendor_id == vendor.id)
    count_result = await db.execute(count_stmt)
    plan_count = count_result.scalar() or 0

    detail = VendorDetail.model_validate(vendor)
    detail.plan_count = plan_count
    return detail


@router.put("/{slug}", response_model=VendorResponse)
async def update_vendor(slug: str, data: VendorUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(Vendor).where(Vendor.slug == slug)
    result = await db.execute(stmt)
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor '{slug}' not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(vendor, key, value)
    await db.flush()
    await db.refresh(vendor)
    return vendor


@router.delete("/{slug}", status_code=204)
async def delete_vendor(slug: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Vendor).where(Vendor.slug == slug)
    result = await db.execute(stmt)
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor '{slug}' not found")
    await db.delete(vendor)
    await db.flush()


@router.get("/{slug}/config-fields")
async def get_vendor_config_fields(slug: str):
    """Get the configuration fields required by a vendor's plugin."""
    from app.plugins.registry import get_plugin

    plugin = get_plugin(slug)
    if not plugin:
        return {"fields": []}

    fields = getattr(plugin, "config_fields", lambda: [])()
    return {"slug": slug, "fields": fields}
