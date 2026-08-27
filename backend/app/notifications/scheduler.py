"""Background jobs:
  * daily digest of "N days before" reminders (cron, Asia/Kathmandu)
  * every-minute check for one-off reminders scheduled at an exact time
"""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from ..config import get_settings
from ..database import SessionLocal
from .service import run_reminders, run_scheduled_reminders

_scheduler: BackgroundScheduler | None = None


def _digest_job() -> None:
    db = SessionLocal()
    try:
        print(f"[scheduler] digest run: {run_reminders(db)}")
    except Exception as exc:  # noqa: BLE001 - never let a job crash the scheduler
        print(f"[scheduler] digest run errored: {exc}")
    finally:
        db.close()


def _scheduled_job() -> None:
    db = SessionLocal()
    try:
        result = run_scheduled_reminders(db)
        if result["processed"]:
            print(f"[scheduler] scheduled reminders: {result}")
    except Exception as exc:  # noqa: BLE001
        print(f"[scheduler] scheduled reminder run errored: {exc}")
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler | None:
    global _scheduler
    settings = get_settings()
    if not settings.scheduler_enabled or _scheduler is not None:
        return _scheduler

    scheduler = BackgroundScheduler(timezone="Asia/Kathmandu")
    scheduler.add_job(
        _digest_job,
        CronTrigger(hour=settings.notify_hour, minute=0),
        id="daily-digest",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        _scheduled_job,
        IntervalTrigger(seconds=60),
        id="scheduled-reminders",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    _scheduler = scheduler
    print(
        f"[scheduler] started; digest at {settings.notify_hour:02d}:00 NPT, "
        "one-off reminders checked every 60s"
    )
    return scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


def scheduler_running() -> bool:
    return _scheduler is not None and _scheduler.running
