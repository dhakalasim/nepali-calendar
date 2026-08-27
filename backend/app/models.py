"""Database models."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Event(Base):
    """An important date. ``ad_date`` is the canonical value; the ``bs_*``
    columns store the same day in Bikram Sambat for display and BS recurrence."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")

    ad_date: Mapped[date] = mapped_column(Date, index=True)
    bs_year: Mapped[int] = mapped_column(Integer)
    bs_month: Mapped[int] = mapped_column(Integer)
    bs_day: Mapped[int] = mapped_column(Integer)

    category: Mapped[str] = mapped_column(String(40), default="personal")
    is_holiday: Mapped[bool] = mapped_column(Boolean, default=False)

    # none | yearly_ad | yearly_bs
    recurrence: Mapped[str] = mapped_column(String(20), default="none")

    notify_days_before: Mapped[int] = mapped_column(Integer, default=1)
    notify_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # user | seed
    source: Mapped[str] = mapped_column(String(20), default="user")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class NotificationLog(Base):
    """One row per (event, occurrence) that has already been notified, so the
    daily job never sends the same reminder twice."""

    __tablename__ = "notification_log"
    __table_args__ = (
        UniqueConstraint("event_id", "occurrence_date", name="uq_notif_event_occurrence"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), index=True
    )
    occurrence_date: Mapped[date] = mapped_column(Date)
    channel: Mapped[str] = mapped_column(String(20), default="email")
    recipients: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="sent")  # sent | logged | failed
    detail: Mapped[str] = mapped_column(Text, default="")
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
