"""Month-grid endpoint: a BS month with every day mapped to its AD date and events."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import nepali_date
from ..crud import list_events
from ..database import get_db
from ..models import Event
from ..recurrence import occurrences_in_range

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


def _event_brief(event: Event) -> dict:
    return {
        "id": event.id,
        "title": event.title,
        "category": event.category,
        "is_holiday": event.is_holiday,
        "recurrence": event.recurrence,
    }


@router.get("")
def get_calendar(
    year: int = Query(..., ge=nepali_date.MIN_BS_YEAR, le=nepali_date.MAX_BS_YEAR - 1),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
) -> dict:
    try:
        days_in_month = nepali_date.days_in_bs_month(year, month)
        month_start, month_end = nepali_date.bs_month_range_ad(year, month)
    except nepali_date.DateOutOfRange as exc:
        raise HTTPException(status_code=400, detail=f"Unsupported BS month: {exc}")

    by_day: dict[date, list[Event]] = defaultdict(list)
    for event in list_events(db):
        for occ in occurrences_in_range(event, month_start, month_end):
            by_day[occ].append(event)

    today = nepali_date.today_npt()
    today_bs = nepali_date.ad_to_bs(today)

    days = []
    for day_num in range(1, days_in_month + 1):
        ad = month_start + timedelta(days=day_num - 1)
        day_events = by_day.get(ad, [])
        weekday = nepali_date.bs_weekday(ad)
        days.append(
            {
                "bs_day": day_num,
                "bs_day_np": nepali_date.to_nepali_digits(day_num),
                "ad_date": ad.isoformat(),
                "ad_day": ad.day,
                "ad_month": ad.month,
                "ad_month_name": ad.strftime("%b"),
                "ad_year": ad.year,
                "weekday": weekday,
                "is_today": ad == today,
                "is_saturday": weekday == 6,
                "is_holiday": any(e.is_holiday for e in day_events),
                "events": [_event_brief(e) for e in day_events],
            }
        )

    prev_year, prev_month = nepali_date.shift_bs_month(year, month, -1)
    next_year, next_month = nepali_date.shift_bs_month(year, month, 1)

    return {
        "bs_year": year,
        "bs_year_np": nepali_date.to_nepali_digits(year),
        "bs_month": month,
        "bs_month_name": nepali_date.BS_MONTHS_EN[month - 1],
        "bs_month_name_np": nepali_date.BS_MONTHS_NP[month - 1],
        "days_in_month": days_in_month,
        "start_weekday": nepali_date.bs_weekday(month_start),
        "month_start_ad": month_start.isoformat(),
        "month_end_ad": month_end.isoformat(),
        "today": {
            "ad_date": today.isoformat(),
            "bs_year": today_bs.year,
            "bs_month": today_bs.month,
            "bs_day": today_bs.day,
            "in_view": today_bs.year == year and today_bs.month == month,
        },
        "prev": {"year": prev_year, "month": prev_month},
        "next": {"year": next_year, "month": next_month},
        "weekdays_en": nepali_date.WEEKDAYS_SHORT_EN,
        "weekdays_np": nepali_date.WEEKDAYS_NP,
        "days": days,
    }
