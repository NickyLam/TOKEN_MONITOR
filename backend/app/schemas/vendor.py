"""Vendor and Plan Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ── Vendor ──────────────────────────────────────────────

class VendorCreate(BaseModel):
    slug: str
    display_name: str
    icon_url: Optional[str] = None
    is_active: bool = True


class VendorUpdate(BaseModel):
    display_name: Optional[str] = None
    icon_url: Optional[str] = None
    is_active: Optional[bool] = None


class VendorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    display_name: str
    icon_url: Optional[str] = None
    is_active: bool
    created_at: datetime


class VendorDetail(VendorResponse):
    plan_count: int = 0


# ── Plan ────────────────────────────────────────────────

class PlanCreate(BaseModel):
    vendor_id: int
    name: str
    plan_type: str  # subscription | token_credits | free_tier
    monthly_cost: Optional[Decimal] = None
    quota_limit: Optional[float] = None
    quota_unit: Optional[str] = None
    billing_day: Optional[int] = None
    renewal_date: Optional[date] = None
    api_key_ref: Optional[str] = None
    extra_config: Optional[dict] = None
    is_active: bool = True
    notes: Optional[str] = None


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    plan_type: Optional[str] = None
    monthly_cost: Optional[Decimal] = None
    quota_limit: Optional[float] = None
    quota_unit: Optional[str] = None
    billing_day: Optional[int] = None
    renewal_date: Optional[date] = None
    api_key_ref: Optional[str] = None
    extra_config: Optional[dict] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vendor_id: int
    name: str
    plan_type: str
    monthly_cost: Optional[Decimal] = None
    quota_limit: Optional[float] = None
    quota_unit: Optional[str] = None
    billing_day: Optional[int] = None
    renewal_date: Optional[date] = None
    api_key_ref: Optional[str] = None
    extra_config: Optional[dict] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PlanDetail(PlanResponse):
    vendor_name: Optional[str] = None
    vendor_slug: Optional[str] = None
    quota_used: Optional[float] = None
    quota_percent: Optional[float] = None
