"""Database operations for events."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from . import nepali_date
from .models import Event, EventReminder
from .schemas import BsDate, EventCreate, EventUpdate, ReminderIn


def _resolve_dates(
    ad_date: date | None, bs: BsDate | None
) -> tuple[date, tuple[int, int, int]]:
    """Return (ad_date, (bs_year, bs_month, bs_day)) from whichever was given."""
    if bs is not None:
        ad = nepali_date.bs_to_ad(bs.year, bs.month, bs.day)
        return ad, (bs.year, bs.month, bs.day)
    if ad_date is not None:
        b = nepali_date.ad_to_bs(ad_date)
        return ad_date, (b.year, b.month, b.day)
    raise ValueError("Either ad_date or bs must be provided")


def _sync_reminders(event: Event, reminders: list[ReminderIn] | None) -> None:
    """Replace the event's *pending* reminders with the supplied list.
    Already-sent reminders are left untouched."""
    if reminders is None:
        return
    for existing in [r for r in event.reminders if r.sent_at is None]:
        event.reminders.remove(existing)  # delete-orphan cascade removes the row
    for item in reminders:
        event.reminders.append(
            EventReminder(
                remind_at=nepali_date.npt_wallclock_to_utc_naive(item.remind_at),
                channels=item.channels,
                status="pending",
            )
        )


def list_events(db: Session) -> list[Event]:
    return list(
        db.scalars(
            select(Event)
            .options(selectinload(Event.reminders))
            .order_by(Event.ad_date, Event.id)
        )
    )


def get_event(db: Session, event_id: int) -> Event | None:
    return db.get(Event, event_id)


def create_event(db: Session, payload: EventCreate) -> Event:
    ad, (by, bm, bd) = _resolve_dates(payload.ad_date, payload.bs)
    event = Event(
        title=payload.title.strip(),
        description=(payload.description or "").strip(),
        ad_date=ad,
        bs_year=by,
        bs_month=bm,
        bs_day=bd,
        category=payload.category,
        recurrence=payload.recurrence,
        notify_days_before=payload.notify_days_before,
        notify_enabled=payload.notify_enabled,
        is_holiday=payload.category in ("holiday", "festival"),
        source="user",
    )
    _sync_reminders(event, payload.reminders)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def update_event(db: Session, event: Event, payload: EventUpdate) -> Event:
    data = payload.model_dump(exclude_unset=True)

    if "bs" in data or "ad_date" in data:
        ad, (by, bm, bd) = _resolve_dates(data.get("ad_date"), payload.bs)
        event.ad_date, event.bs_year, event.bs_month, event.bs_day = ad, by, bm, bd

    for field in (
        "title",
        "description",
        "category",
        "recurrence",
        "notify_days_before",
        "notify_enabled",
    ):
        if field in data and data[field] is not None:
            setattr(event, field, data[field].strip() if field == "title" else data[field])

    if "reminders" in data:
        _sync_reminders(event, payload.reminders)

    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event: Event) -> None:
    db.delete(event)
    db.commit()
