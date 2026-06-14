"""Vendor and Plan ORM models."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    icon_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    plans: Mapped[list["Plan"]] = relationship(
        "Plan", back_populates="vendor", cascade="all, delete-orphan"
    )


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    # subscription | token_credits | free_tier
    plan_type: Mapped[str] = mapped_column(String(32), nullable=False)

    monthly_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    quota_limit: Mapped[Optional[float]] = mapped_column(nullable=True)
    # requests | tokens | credits | dollars | messages
    quota_unit: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    billing_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-28
    renewal_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    api_key_ref: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    extra_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="plans")
