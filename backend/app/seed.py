"""Load the bundled Nepali holidays / festivals into the database.

Idempotent: running it again only inserts rows that are missing. Run with:

    python -m app.seed
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import nepali_date
from .database import SessionLocal, init_db
from .models import Event

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "holidays.json"


def seed(db: Session) -> dict:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    current_bs_year = nepali_date.today_bs().year
    added = 0
    skipped = 0

    for item in data.get("recurring_bs", []):
        exists = db.scalar(
            select(Event.id).where(
                Event.source == "seed",
                Event.title == item["title"],
                Event.recurrence == "yearly_bs",
                Event.bs_month == item["bs_month"],
                Event.bs_day == item["bs_day"],
            )
        )
        if exists is not None:
            skipped += 1
            continue
        ad = nepali_date.bs_to_ad(current_bs_year, item["bs_month"], item["bs_day"])
        db.add(
            Event(
                title=item["title"],
                description=item.get("description", ""),
                ad_date=ad,
                bs_year=current_bs_year,
                bs_month=item["bs_month"],
                bs_day=item["bs_day"],
                category=item.get("category", "holiday"),
                is_holiday=True,
                recurrence="yearly_bs",
                notify_days_before=item.get("notify_days_before", 1),
                notify_enabled=True,
                source="seed",
            )
        )
        added += 1

    for item in data.get("dated", []):
        ad = date.fromisoformat(item["ad_date"])
        exists = db.scalar(
            select(Event.id).where(
                Event.source == "seed",
                Event.title == item["title"],
                Event.ad_date == ad,
            )
        )
        if exists is not None:
            skipped += 1
            continue
        b = nepali_date.ad_to_bs(ad)
        db.add(
            Event(
                title=item["title"],
                description=item.get("description", ""),
                ad_date=ad,
                bs_year=b.year,
                bs_month=b.month,
                bs_day=b.day,
                category=item.get("category", "festival"),
                is_holiday=item.get("is_holiday", True),
                recurrence="none",
                notify_days_before=item.get("notify_days_before", 1),
                notify_enabled=True,
                source="seed",
            )
        )
        added += 1

    db.commit()
    return {"added": added, "skipped": skipped}


def main() -> None:
    init_db()
    with SessionLocal() as db:
        result = seed(db)
    print(f"[seed] holidays loaded: {result}")


if __name__ == "__main__":
    main()
