"""Endpoints to inspect and trigger reminders."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import NotificationLog
from ..notifications.scheduler import scheduler_running
from ..notifications.service import preview_reminders, run_reminders

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/status")
def status() -> dict:
    settings = get_settings()
    return {
        "email_enabled": settings.email_enabled,
        "recipients": settings.notify_recipients,
        "notify_hour": settings.notify_hour,
        "scheduler_running": scheduler_running(),
        "smtp_host": settings.smtp_host or None,
    }


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
