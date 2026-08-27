"""Background job that runs the reminder digest once a day (Asia/Kathmandu)."""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from ..config import get_settings
from ..database import SessionLocal
from .service import run_reminders

_scheduler: BackgroundScheduler | None = None


def _run_job() -> None:
    db = SessionLocal()
    try:
        result = run_reminders(db)
        print(f"[scheduler] reminder run: {result}")
    except Exception as exc:  # noqa: BLE001 - never let the job crash the scheduler
        print(f"[scheduler] reminder run errored: {exc}")
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler | None:
    global _scheduler
    settings = get_settings()
    if not settings.scheduler_enabled or _scheduler is not None:
        return _scheduler

    scheduler = BackgroundScheduler(timezone="Asia/Kathmandu")
    scheduler.add_job(
        _run_job,
        CronTrigger(hour=settings.notify_hour, minute=0),
        id="daily-reminders",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    _scheduler = scheduler
    print(f"[scheduler] started; daily reminders at {settings.notify_hour:02d}:00 NPT")
    return scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


def scheduler_running() -> bool:
    return _scheduler is not None and _scheduler.running
