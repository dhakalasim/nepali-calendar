"""Bikram Sambat <-> Gregorian helpers built on top of ``nepali_datetime``."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import nepali_datetime

# Month names, index 0 == month 1 (Baishakh). We keep our own list rather than
# relying on strftime so the backend and frontend always agree.
BS_MONTHS_EN = [
    "Baishakh", "Jestha", "Ashadh", "Shrawan", "Bhadra", "Ashwin",
    "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra",
]
BS_MONTHS_NP = [
    "वैशाख", "जेठ", "असार", "साउन", "भदौ", "असोज",
    "कात्तिक", "मंसिर", "पुष", "माघ", "फागुन", "चैत",
]

# Weekday index: Sunday == 0 ... Saturday == 6 (Nepali convention).
WEEKDAYS_EN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
WEEKDAYS_SHORT_EN = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
WEEKDAYS_NP = ["आइतबार", "सोमबार", "मंगलबार", "बुधबार", "बिहीबार", "शुक्रबार", "शनिबार"]

MIN_BS_YEAR: int = getattr(nepali_datetime, "MINYEAR", 1975)
MAX_BS_YEAR: int = getattr(nepali_datetime, "MAXYEAR", 2100)

NPT = timezone(timedelta(hours=5, minutes=45))

_NP_DIGITS = "०१२३४५६७८९"


class DateOutOfRange(ValueError):
    """Raised when a BS date is outside the range the converter supports."""


def to_nepali_digits(value: object) -> str:
    return "".join(_NP_DIGITS[int(ch)] if ch.isdigit() else ch for ch in str(value))


def today_npt() -> date:
    """Current calendar date in Nepal, independent of the server timezone."""
    return datetime.now(NPT).date()


def now_utc_naive() -> datetime:
    """Current instant as a naive UTC datetime (how reminders are stored)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def npt_wallclock_to_utc_naive(dt: datetime) -> datetime:
    """Take a datetime the user picked (Nepal wall-clock, usually naive) and
    return the matching naive-UTC value for storage/comparison."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=NPT)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def ad_to_bs(d: date) -> nepali_datetime.date:
    try:
        return nepali_datetime.date.from_datetime_date(d)
    except Exception as exc:  # noqa: BLE001 - library raises bare ValueError/Exception
        raise DateOutOfRange(str(exc)) from exc


def bs_to_ad(year: int, month: int, day: int) -> date:
    try:
        return nepali_datetime.date(year, month, day).to_datetime_date()
    except Exception as exc:  # noqa: BLE001
        raise DateOutOfRange(str(exc)) from exc


def today_bs() -> nepali_datetime.date:
    return ad_to_bs(today_npt())


def bs_weekday(d: date) -> int:
    """Weekday of an AD date with Sunday == 0 ... Saturday == 6."""
    return d.isoweekday() % 7


def days_in_bs_month(year: int, month: int) -> int:
    first = bs_to_ad(year, month, 1)
    if month == 12:
        nxt = bs_to_ad(year + 1, 1, 1)
    else:
        nxt = bs_to_ad(year, month + 1, 1)
    return (nxt - first).days


def bs_month_range_ad(year: int, month: int) -> tuple[date, date]:
    """Inclusive AD span [first day, last day] covering a BS month."""
    start = bs_to_ad(year, month, 1)
    end = start + timedelta(days=days_in_bs_month(year, month) - 1)
    return start, end


def clamp_bs_day(year: int, month: int, day: int) -> int:
    return min(day, days_in_bs_month(year, month))


def shift_bs_month(year: int, month: int, delta: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def bs_label(year: int, month: int, day: int, *, nepali: bool = False) -> str:
    if nepali:
        name = BS_MONTHS_NP[month - 1]
        return f"{name} {to_nepali_digits(day)}, {to_nepali_digits(year)}"
    return f"{BS_MONTHS_EN[month - 1]} {day}, {year}"


def ad_label(d: date) -> str:
    return d.strftime("%B %-d, %Y") if hasattr(d, "strftime") else str(d)
