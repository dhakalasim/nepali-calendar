"""Pydantic request/response models."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator

Category = Literal[
    "personal", "holiday", "festival", "birthday", "anniversary", "meeting", "other"
]
Recurrence = Literal["none", "yearly_ad", "yearly_bs"]
ReminderChannel = Literal["all", "email", "sms", "telegram"]


class ReminderIn(BaseModel):
    # A moment in Nepal wall-clock time, e.g. "2026-09-01T14:30".
    remind_at: datetime
    channels: ReminderChannel = "all"


class ReminderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    remind_at: datetime
    sent_at: Optional[datetime] = None
    status: str
    channels: str

    @field_serializer("remind_at", "sent_at", when_used="json")
    def _as_utc(self, value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        # stored naive UTC -> emit an explicit-offset ISO string
        return value.replace(tzinfo=timezone.utc).isoformat()


class BsDate(BaseModel):
    year: int = Field(ge=1, le=3000)
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=32)


class EventBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    category: Category = "personal"
    recurrence: Recurrence = "none"
    notify_days_before: int = Field(default=1, ge=0, le=365)
    notify_enabled: bool = True


class EventCreate(EventBase):
    ad_date: Optional[date] = None
    bs: Optional[BsDate] = None
    reminders: Optional[list[ReminderIn]] = None

    @model_validator(mode="after")
    def _one_date(self) -> "EventCreate":
        if self.ad_date is None and self.bs is None:
            raise ValueError("Provide either 'ad_date' or 'bs'")
        return self


class EventUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[Category] = None
    recurrence: Optional[Recurrence] = None
    notify_days_before: Optional[int] = Field(default=None, ge=0, le=365)
    notify_enabled: Optional[bool] = None
    ad_date: Optional[date] = None
    bs: Optional[BsDate] = None
    reminders: Optional[list[ReminderIn]] = None


class EventOut(EventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ad_date: date
    bs_year: int
    bs_month: int
    bs_day: int
    is_holiday: bool
    source: str
    reminders: list[ReminderOut] = []
    created_at: datetime
    updated_at: datetime


class EventOccurrence(BaseModel):
    event: EventOut
    occurrence_ad: date
    occurrence_bs: BsDate
    days_until: int


class SendReminderRequest(BaseModel):
    channels: ReminderChannel = "all"


class ConvertResult(BaseModel):
    ad_date: date
    bs: BsDate
    bs_month_name: str
    bs_month_name_np: str
    weekday: int
    weekday_name: str


class NotificationSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notify_emails: str
    notify_phones: str
    notify_telegram: str
    email_enabled: bool
    sms_enabled: bool
    telegram_enabled: bool


class NotificationSettingsUpdate(BaseModel):
    notify_emails: Optional[str] = None
    notify_phones: Optional[str] = None
    notify_telegram: Optional[str] = None
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    telegram_enabled: Optional[bool] = None


class TestNotificationRequest(BaseModel):
    channels: Optional[list[Literal["email", "sms", "telegram"]]] = None
