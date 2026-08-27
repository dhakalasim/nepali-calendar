"""Expand an event into concrete calendar occurrences."""

from __future__ import annotations

from datetime import date

from . import nepali_date
from .models import Event


def occurrences_in_range(event: Event, start: date, end: date) -> list[date]:
    """All AD dates on which ``event`` occurs within [start, end] (inclusive)."""
    if start > end:
        return []

    if event.recurrence == "none":
        return [event.ad_date] if start <= event.ad_date <= end else []

    if event.recurrence == "yearly_ad":
        out: list[date] = []
        for year in range(start.year, end.year + 1):
            try:
                occ = date(year, event.ad_date.month, event.ad_date.day)
            except ValueError:  # Feb 29 in a non-leap year
                occ = date(year, event.ad_date.month, 28)
            if start <= occ <= end:
                out.append(occ)
        return out

    if event.recurrence == "yearly_bs":
        out = []
        try:
            start_bs_year = nepali_date.ad_to_bs(start).year
            end_bs_year = nepali_date.ad_to_bs(end).year
        except nepali_date.DateOutOfRange:
            return []
        for bs_year in range(start_bs_year, end_bs_year + 1):
            try:
                day = nepali_date.clamp_bs_day(bs_year, event.bs_month, event.bs_day)
                occ = nepali_date.bs_to_ad(bs_year, event.bs_month, day)
            except nepali_date.DateOutOfRange:
                continue
            if start <= occ <= end:
                out.append(occ)
        return out

    return []


def next_occurrence(event: Event, on_or_after: date, *, horizon_years: int = 3) -> date | None:
    end = date(
        on_or_after.year + horizon_years,
        on_or_after.month,
        min(on_or_after.day, 28),
    )
    occ = occurrences_in_range(event, on_or_after, end)
    return occ[0] if occ else None
