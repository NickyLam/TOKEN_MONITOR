"""Dashboard Pydantic schemas."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class QuotaStatus(BaseModel):
    plan_id: int
    plan_name: str
    vendor_slug: str
    vendor_name: str
    plan_type: str
    quota_used: Optional[float] = None
    quota_total: Optional[float] = None
    quota_unit: Optional[str] = None
    quota_percent: Optional[float] = None
    monthly_cost: Optional[float] = None
    renewal_date: Optional[date] = None
    days_until_renewal: Optional[int] = None


class VendorSpendItem(BaseModel):
    vendor_slug: str
    vendor_name: str
    spend: float = 0.0
    subscription_cost: float = 0.0


class SpendOverview(BaseModel):
    total_spend: float = 0.0
    budget: Optional[float] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    vendor_breakdown: list[VendorSpendItem] = []


class DailySpend(BaseModel):
    date: date
    total: float = 0.0
    by_vendor: dict[str, float] = {}


class UsageTrends(BaseModel):
    daily_spend: list[DailySpend] = []
    forecast_total: Optional[float] = None
    days_projected: int = 0
