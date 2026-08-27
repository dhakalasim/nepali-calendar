"""Decide which reminders are due and send the digest."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import nepali_date
from ..models import Event, NotificationLog
from ..recurrence import next_occurrence
from .email import send_email
from .templates import DueItem, render_digest


def _collect_due(db: Session, on_date: date, *, ignore_log: bool) -> list[DueItem]:
    due: list[DueItem] = []
    events = db.scalars(select(Event).where(Event.notify_enabled.is_(True)))
    for event in events:
        occ = next_occurrence(event, on_date)
        if occ is None:
            continue
        days_until = (occ - on_date).days
        if days_until > event.notify_days_before:
            continue
        if not ignore_log:
            already = db.scalar(
                select(NotificationLog.id).where(
                    NotificationLog.event_id == event.id,
                    NotificationLog.occurrence_date == occ,
                )
            )
            if already is not None:
                continue
        due.append(DueItem(event=event, occurrence=occ, days_until=days_until))
    due.sort(key=lambda d: (d.occurrence, d.event.title))
    return due


def preview_reminders(db: Session, on_date: date | None = None) -> dict:
    """What the next run would send - no email, no log writes."""
    on_date = on_date or nepali_date.today_npt()
    due = _collect_due(db, on_date, ignore_log=True)
    subject = ""
    html = ""
    if due:
        subject, _text, html = render_digest(due, on_date)
    return {
        "as_of": on_date.isoformat(),
        "count": len(due),
        "subject": subject,
        "html": html,
        "items": [
            {
                "event_id": d.event.id,
                "title": d.event.title,
                "occurrence_ad": d.occurrence.isoformat(),
                "days_until": d.days_until,
                "notify_days_before": d.event.notify_days_before,
            }
            for d in due
        ],
    }


def run_reminders(db: Session, on_date: date | None = None) -> dict:
    """Send the digest for everything now inside its reminder window."""
    on_date = on_date or nepali_date.today_npt()
    due = _collect_due(db, on_date, ignore_log=False)
    if not due:
        return {"as_of": on_date.isoformat(), "sent": False, "count": 0, "items": []}

    subject, text, html = render_digest(due, on_date)
    status, detail = send_email(subject, text, html)

    if status in ("sent", "logged"):
        for item in due:
            db.add(
                NotificationLog(
                    event_id=item.event.id,
                    occurrence_date=item.occurrence,
                    channel="email",
                    recipients=detail if status == "sent" else "",
                    status=status,
                    detail="" if status == "sent" else detail,
                )
            )
        db.commit()

    return {
        "as_of": on_date.isoformat(),
        "sent": status in ("sent", "logged"),
        "status": status,
        "detail": detail,
        "count": len(due),
        "items": [
            {
                "event_id": d.event.id,
                "title": d.event.title,
                "occurrence_ad": d.occurrence.isoformat(),
                "days_until": d.days_until,
            }
            for d in due
        ],
    }
