"""Alert rule and event ORM models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("plans.id", ondelete="SET NULL"), nullable=True
    )
    # quota_percent | spend_dollars | plan_expiring_days | daily_spend_spike | token_threshold
    rule_type: Mapped[str] = mapped_column(String(64), nullable=False)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_unit: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_rule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False
    )
    plan_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("plans.id", ondelete="SET NULL"), nullable=True
    )
    # info | warning | critical
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    evaluated_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
