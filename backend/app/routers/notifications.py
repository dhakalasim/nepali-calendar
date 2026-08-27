"""Endpoints to inspect, configure, and trigger reminders."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import NotificationLog
from ..notifications.scheduler import scheduler_running
from ..notifications.service import (
    preview_reminders,
    run_reminders,
    run_scheduled_reminders,
    send_test,
)
from ..notifications.settings_store import (
    get_app_settings,
    get_email_targets,
    get_sms_targets,
    get_telegram_targets,
    normalize_emails,
    normalize_phones,
    normalize_telegram,
)
from ..notifications.telegram import get_recent_chats
from ..schemas import (
    NotificationSettingsOut,
    NotificationSettingsUpdate,
    TestNotificationRequest,
)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/status")
def status(db: Session = Depends(get_db)) -> dict:
    s = get_settings()
    app = get_app_settings(db)
    email_targets = get_email_targets(db)
    sms_targets = get_sms_targets(db)
    tg_targets = get_telegram_targets(db)
    return {
        "scheduler_running": scheduler_running(),
        "notify_hour": s.notify_hour,
        "email": {
            "provider_configured": s.smtp_configured,
            "enabled": app.email_enabled,
            "recipients": email_targets,
            "active": bool(app.email_enabled and email_targets),
        },
        "sms": {
            "provider_configured": s.sms_configured,
            "provider": s.resolved_sms_provider,
            "enabled": app.sms_enabled,
            "recipients": sms_targets,
            "active": bool(app.sms_enabled and sms_targets),
        },
        "telegram": {
            "provider_configured": s.telegram_configured,
            "enabled": app.telegram_enabled,
            "recipients": tg_targets,
            "active": bool(app.telegram_enabled and tg_targets),
        },
    }


@router.get("/settings", response_model=NotificationSettingsOut)
def get_notification_settings(db: Session = Depends(get_db)):
    return get_app_settings(db)


@router.put("/settings", response_model=NotificationSettingsOut)
def update_notification_settings(
    payload: NotificationSettingsUpdate, db: Session = Depends(get_db)
):
    row = get_app_settings(db)
    data = payload.model_dump(exclude_unset=True)
    try:
        if "notify_emails" in data:
            row.notify_emails = normalize_emails(data["notify_emails"] or "")
        if "notify_phones" in data:
            row.notify_phones = normalize_phones(data["notify_phones"] or "")
        if "notify_telegram" in data:
            row.notify_telegram = normalize_telegram(data["notify_telegram"] or "")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if "email_enabled" in data:
        row.email_enabled = bool(data["email_enabled"])
    if "sms_enabled" in data:
        row.sms_enabled = bool(data["sms_enabled"])
    if "telegram_enabled" in data:
        row.telegram_enabled = bool(data["telegram_enabled"])
    db.commit()
    db.refresh(row)
    return row


@router.post("/test")
def test(payload: TestNotificationRequest, db: Session = Depends(get_db)) -> dict:
    return send_test(db, payload.channels)


@router.get("/telegram/chats")
def telegram_chats() -> dict:
    """Chats that recently messaged the bot - use to fill in the chat id.
    (Send your bot any message first, then call this.)"""
    s = get_settings()
    if not s.telegram_configured:
        raise HTTPException(status_code=400, detail="TELEGRAM_BOT_TOKEN is not set")
    return {"chats": get_recent_chats()}


@router.get("/preview")
def preview(
    as_of: date | None = Query(default=None, description="Pretend 'today' is this AD date"),
    db: Session = Depends(get_db),
) -> dict:
    return preview_reminders(db, as_of)


@router.post("/run")
def run(
    as_of: date | None = Query(default=None, description="Pretend 'today' is this AD date"),
    db: Session = Depends(get_db),
) -> dict:
    return run_reminders(db, as_of)


@router.post("/run-scheduled")
def run_scheduled(db: Session = Depends(get_db)) -> dict:
    """Process any one-off reminders that are due now (also runs every 60s)."""
    return run_scheduled_reminders(db)


@router.get("/log")
def log(limit: int = Query(default=50, ge=1, le=500), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(
        select(NotificationLog).order_by(NotificationLog.sent_at.desc()).limit(limit)
    )
    return [
        {
            "id": r.id,
            "event_id": r.event_id,
            "occurrence_date": r.occurrence_date.isoformat(),
            "channel": r.channel,
            "status": r.status,
            "recipients": r.recipients,
            "detail": r.detail,
            "sent_at": r.sent_at.isoformat() if r.sent_at else None,
        }
        for r in rows
    ]
