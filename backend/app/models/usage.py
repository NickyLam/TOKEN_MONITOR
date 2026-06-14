"""Usage record ORM model (append-only)."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vendor_slug: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # quota_snapshot | token_usage | cost_snapshot
    record_type: Mapped[str] = mapped_column(String(32), nullable=False)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )
    period_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    period_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Subscription quota fields
    quota_used: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quota_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Token usage fields
    input_tokens: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    cache_read_tokens: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)
    cache_write_tokens: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)

    total_cost_usd: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6), nullable=True)
    request_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Metadata
    model_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    raw_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
