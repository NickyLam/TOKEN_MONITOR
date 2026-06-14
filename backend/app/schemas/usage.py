"""Usage record Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UsageRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    vendor_slug: str
    record_type: str
    recorded_at: datetime
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    quota_used: Optional[float] = None
    quota_total: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cache_read_tokens: Optional[int] = None
    cache_write_tokens: Optional[int] = None
    total_cost_usd: Optional[Decimal] = None
    request_count: Optional[int] = None
    model_name: Optional[str] = None


class TokenBreakdownItem(BaseModel):
    label: str  # model name or date
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    cost_usd: float = 0.0


class ModelBreakdownItem(BaseModel):
    model: str
    request_count: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
