"""Polling Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PollingConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vendor_slug: str
    is_enabled: bool
    interval_minutes: int
    last_polled_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int
    created_at: datetime
    updated_at: datetime


class PollingConfigUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    interval_minutes: Optional[int] = None


class PollingStatus(BaseModel):
    vendor_slug: str
    is_enabled: bool
    interval_minutes: int
    last_polled_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int
    display_name: Optional[str] = None
