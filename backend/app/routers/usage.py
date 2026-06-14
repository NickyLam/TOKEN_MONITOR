"""Usage query endpoints."""

import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.usage import UsageRecord
from app.schemas.usage import (
    ModelBreakdownItem,
    TokenBreakdownItem,
    UsageRecordResponse,
)

router = APIRouter(prefix="/api/usage", tags=["usage"])


@router.get("", response_model=dict)
async def list_usage(
    plan_id: Optional[int] = Query(None),
    vendor_slug: Optional[str] = Query(None),
    record_type: Optional[str] = Query(None),
    start: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UsageRecord)
    count_stmt = select(func.count()).select_from(UsageRecord)

    if plan_id is not None:
        stmt = stmt.where(UsageRecord.plan_id == plan_id)
        count_stmt = count_stmt.where(UsageRecord.plan_id == plan_id)
    if vendor_slug:
        stmt = stmt.where(UsageRecord.vendor_slug == vendor_slug)
        count_stmt = count_stmt.where(UsageRecord.vendor_slug == vendor_slug)
    if record_type:
        stmt = stmt.where(UsageRecord.record_type == record_type)
        count_stmt = count_stmt.where(UsageRecord.record_type == record_type)
    if start:
        start_dt = datetime.fromisoformat(start)
        stmt = stmt.where(UsageRecord.recorded_at >= start_dt)
        count_stmt = count_stmt.where(UsageRecord.recorded_at >= start_dt)
    if end:
        end_dt = datetime.fromisoformat(end + "T23:59:59")
        stmt = stmt.where(UsageRecord.recorded_at <= end_dt)
        count_stmt = count_stmt.where(UsageRecord.recorded_at <= end_dt)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = stmt.order_by(UsageRecord.recorded_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    records = result.scalars().all()

    return {
        "data": [UsageRecordResponse.model_validate(r) for r in records],
        "total": total,
        "page": page,
        "page_size": size,
    }


@router.get("/token-breakdown", response_model=list[TokenBreakdownItem])
async def token_breakdown(
    plan_id: Optional[int] = Query(None),
    group_by: str = Query("model", pattern="^(model|day)$"),
    db: AsyncSession = Depends(get_db),
):
    if group_by == "model":
        stmt = (
            select(
                UsageRecord.model_name.label("label"),
                func.coalesce(func.sum(UsageRecord.input_tokens), 0).label("input_tokens"),
                func.coalesce(func.sum(UsageRecord.output_tokens), 0).label("output_tokens"),
                func.coalesce(func.sum(UsageRecord.cache_read_tokens), 0).label("cache_read"),
                func.coalesce(func.sum(UsageRecord.cache_write_tokens), 0).label("cache_write"),
                func.coalesce(func.sum(UsageRecord.total_cost_usd), 0).label("cost"),
            )
            .where(UsageRecord.record_type == "token_usage")
        )
        if plan_id is not None:
            stmt = stmt.where(UsageRecord.plan_id == plan_id)
        stmt = stmt.group_by(UsageRecord.model_name).order_by(func.sum(UsageRecord.total_cost_usd).desc())
    else:
        stmt = (
            select(
                func.date(UsageRecord.recorded_at).label("label"),
                func.coalesce(func.sum(UsageRecord.input_tokens), 0).label("input_tokens"),
                func.coalesce(func.sum(UsageRecord.output_tokens), 0).label("output_tokens"),
                func.coalesce(func.sum(UsageRecord.cache_read_tokens), 0).label("cache_read"),
                func.coalesce(func.sum(UsageRecord.cache_write_tokens), 0).label("cache_write"),
                func.coalesce(func.sum(UsageRecord.total_cost_usd), 0).label("cost"),
            )
            .where(UsageRecord.record_type == "token_usage")
        )
        if plan_id is not None:
            stmt = stmt.where(UsageRecord.plan_id == plan_id)
        stmt = stmt.group_by("label").order_by("label")

    result = await db.execute(stmt)
    return [
        TokenBreakdownItem(
            label=row.label or "unknown",
            input_tokens=int(row.input_tokens),
            output_tokens=int(row.output_tokens),
            cache_read_tokens=int(row.cache_read),
            cache_write_tokens=int(row.cache_write),
            cost_usd=float(row.cost),
        )
        for row in result
    ]


@router.get("/model-breakdown", response_model=list[ModelBreakdownItem])
async def model_breakdown(
    plan_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(
            UsageRecord.model_name,
            func.coalesce(func.sum(UsageRecord.request_count), 0).label("request_count"),
            func.coalesce(
                func.sum(UsageRecord.input_tokens) + func.sum(UsageRecord.output_tokens), 0
            ).label("total_tokens"),
            func.coalesce(func.sum(UsageRecord.total_cost_usd), 0).label("cost"),
        )
        .where(UsageRecord.record_type == "token_usage")
    )
    if plan_id is not None:
        stmt = stmt.where(UsageRecord.plan_id == plan_id)
    stmt = stmt.group_by(UsageRecord.model_name).order_by(func.sum(UsageRecord.total_cost_usd).desc())

    result = await db.execute(stmt)
    return [
        ModelBreakdownItem(
            model=row.model_name or "unknown",
            request_count=int(row.request_count),
            total_tokens=int(row.total_tokens),
            cost_usd=float(row.cost),
        )
        for row in result
    ]


@router.get("/export")
async def export_usage(
    plan_id: Optional[int] = Query(None),
    vendor_slug: Optional[str] = Query(None),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UsageRecord)
    if plan_id is not None:
        stmt = stmt.where(UsageRecord.plan_id == plan_id)
    if vendor_slug:
        stmt = stmt.where(UsageRecord.vendor_slug == vendor_slug)
    if start:
        stmt = stmt.where(UsageRecord.recorded_at >= datetime.fromisoformat(start))
    if end:
        stmt = stmt.where(UsageRecord.recorded_at <= datetime.fromisoformat(end + "T23:59:59"))
    stmt = stmt.order_by(UsageRecord.recorded_at.desc())

    result = await db.execute(stmt)
    records = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "plan_id", "vendor_slug", "record_type", "recorded_at",
        "input_tokens", "output_tokens", "total_cost_usd", "model_name", "request_count",
    ])
    for r in records:
        writer.writerow([
            r.id, r.plan_id, r.vendor_slug, r.record_type, r.recorded_at,
            r.input_tokens, r.output_tokens, r.total_cost_usd, r.model_name, r.request_count,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=usage_export.csv"},
    )
