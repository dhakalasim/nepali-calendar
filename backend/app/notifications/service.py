"""Decide which reminders are due and deliver the digest over each channel."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import nepali_date
from ..models import Event, EventReminder, NotificationLog
from ..recurrence import next_occurrence
from .email import send_email
from .settings_store import get_app_settings, get_email_targets, get_sms_targets
from .sms import send_sms
from .templates import DueItem, render_digest, render_sms

_OK = ("sent", "logged")


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


def _due_items_json(due: list[DueItem]) -> list[dict]:
    return [
        {
            "event_id": d.event.id,
            "title": d.event.title,
            "occurrence_ad": d.occurrence.isoformat(),
            "days_until": d.days_until,
            "notify_days_before": d.event.notify_days_before,
        }
        for d in due
    ]


def preview_reminders(db: Session, on_date: date | None = None) -> dict:
    """What the next run would send - no delivery, no log writes."""
    on_date = on_date or nepali_date.today_npt()
    due = _collect_due(db, on_date, ignore_log=True)
    app = get_app_settings(db)
    subject = html = ""
    if due:
        subject, _text, html = render_digest(due, on_date)
    return {
        "as_of": on_date.isoformat(),
        "count": len(due),
        "subject": subject,
        "html": html,
        "email_targets": get_email_targets(db) if app.email_enabled else [],
        "sms_targets": get_sms_targets(db) if app.sms_enabled else [],
        "items": _due_items_json(due),
    }


def _deliver(db: Session, due: list[DueItem], on_date: date) -> dict[str, tuple[str, str]]:
    """Send the digest over every enabled + addressed channel."""
    app = get_app_settings(db)
    results: dict[str, tuple[str, str]] = {}

    email_targets = get_email_targets(db)
    if app.email_enabled and email_targets:
        subject, text, html = render_digest(due, on_date)
        results["email"] = send_email(subject, text, html, email_targets)

    sms_targets = get_sms_targets(db)
    if app.sms_enabled and sms_targets:
        results["sms"] = send_sms(render_sms(due, on_date), sms_targets)

    return results


def run_reminders(db: Session, on_date: date | None = None) -> dict:
    on_date = on_date or nepali_date.today_npt()
    due = _collect_due(db, on_date, ignore_log=False)
    if not due:
        return {"as_of": on_date.isoformat(), "sent": False, "count": 0,
                "channels": {}, "items": []}

    results = _deliver(db, due, on_date)
    channels = {c: {"status": s, "detail": d} for c, (s, d) in results.items()}

    if not results:
        # Nothing is enabled/addressed yet - do NOT record, so these reminders
        # still fire once the user sets a recipient.
        return {"as_of": on_date.isoformat(), "sent": False, "count": len(due),
                "channels": {}, "note": "No delivery channel is enabled and addressed",
                "items": _due_items_json(due)}

    delivered = any(s in _OK for s, _ in results.values())
    if delivered:
        label = "+".join(sorted(results))[:20]
        detail = "; ".join(f"{c}:{s}" for c, (s, d) in results.items())
        recips = "; ".join(f"{c}:{d}" for c, (s, d) in results.items() if s == "sent")
        status = "sent" if any(s == "sent" for s, _ in results.values()) else "logged"
        for item in due:
            db.add(
                NotificationLog(
                    event_id=item.event.id,
                    occurrence_date=item.occurrence,
                    channel=label,
                    recipients=recips,
                    status=status,
                    detail=detail,
                )
            )
        db.commit()

    return {
        "as_of": on_date.isoformat(),
        "sent": delivered,
        "count": len(due),
        "channels": channels,
        "items": _due_items_json(due),
    }


def _channels_for(choice: str) -> set[str]:
    return {"email", "sms"} if choice == "all" else {choice}


def _deliver_now(db: Session, due: list[DueItem], on_date: date, want: set[str]) -> dict:
    """Send `due` right now over the requested channels that have a recipient.
    Ignores the per-channel enable toggles - this is an explicit action."""
    results: dict[str, tuple[str, str]] = {}
    if "email" in want:
        targets = get_email_targets(db)
        if targets:
            subject, text, html = render_digest(due, on_date)
            results["email"] = send_email(subject, text, html, targets)
    if "sms" in want:
        targets = get_sms_targets(db)
        if targets:
            results["sms"] = send_sms(render_sms(due, on_date), targets)
    return results


def send_event_reminder(db: Session, event: Event, channels: str = "all") -> dict:
    """Deliver a reminder for a single event immediately (email and/or text)."""
    on_date = nepali_date.today_npt()
    occ = next_occurrence(event, on_date) or event.ad_date
    due = [DueItem(event=event, occurrence=occ, days_until=(occ - on_date).days)]
    results = _deliver_now(db, due, on_date, _channels_for(channels))
    return {
        "event_id": event.id,
        "sent": any(s in _OK for s, _ in results.values()),
        "channels": {c: {"status": s, "detail": d} for c, (s, d) in results.items()},
        "note": None if results else "No recipient set for the requested channel(s)",
    }


def run_scheduled_reminders(db: Session, now: datetime | None = None) -> dict:
    """Fire every one-off EventReminder whose time has arrived."""
    now = now or nepali_date.now_utc_naive()
    rows = (
        db.scalars(
            select(EventReminder)
            .where(EventReminder.sent_at.is_(None), EventReminder.remind_at <= now)
            .order_by(EventReminder.remind_at)
        )
        .all()
    )
    processed = []
    for row in rows:
        result = send_event_reminder(db, row.event, row.channels)
        row.sent_at = now
        row.status = "sent" if result["sent"] else "failed"
        row.detail = (
            "; ".join(f"{c}:{v['status']}" for c, v in result["channels"].items())
            or result.get("note")
            or "no channel"
        )
        processed.append(
            {"reminder_id": row.id, "event": row.event.title, "status": row.status}
        )
    if processed:
        db.commit()
    return {"processed": len(processed), "items": processed}


def send_test(db: Session, channels: list[str] | None = None) -> dict:
    """Send a one-off test message now. Ignores the enable toggles but still
    needs a recipient. No dedup, nothing written to the log."""
    on_date = nepali_date.today_npt()
    bs = nepali_date.today_bs()
    text = (
        f"Test from Nepali Calendar - {nepali_date.bs_label(bs.year, bs.month, bs.day)} "
        f"BS / {on_date.strftime('%A, %b %d, %Y')}. If you got this, reminders work."
    )
    want = set(channels) if channels else {"email", "sms"}
    out: dict[str, dict] = {}

    if "email" in want:
        targets = get_email_targets(db)
        if not targets:
            out["email"] = {"status": "skipped", "detail": "No recipient email set"}
        else:
            status, detail = send_email(
                "Nepali Calendar - test reminder", text, f"<p>{text}</p>", targets
            )
            out["email"] = {"status": status, "detail": detail}

    if "sms" in want:
        targets = get_sms_targets(db)
        if not targets:
            out["sms"] = {"status": "skipped", "detail": "No phone number set"}
        else:
            status, detail = send_sms(text, targets)
            out["sms"] = {"status": status, "detail": detail}

    return {"channels": out}
