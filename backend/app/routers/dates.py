"""Small date utilities: today, and BS <-> AD conversion."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from .. import nepali_date
from ..schemas import BsDate, ConvertResult

router = APIRouter(prefix="/api", tags=["dates"])


def _describe(ad: date) -> ConvertResult:
    b = nepali_date.ad_to_bs(ad)
    weekday = nepali_date.bs_weekday(ad)
    return ConvertResult(
        ad_date=ad,
        bs=BsDate(year=b.year, month=b.month, day=b.day),
        bs_month_name=nepali_date.BS_MONTHS_EN[b.month - 1],
        bs_month_name_np=nepali_date.BS_MONTHS_NP[b.month - 1],
        weekday=weekday,
        weekday_name=nepali_date.WEEKDAYS_EN[weekday],
    )


@router.get("/today", response_model=ConvertResult)
def today() -> ConvertResult:
    return _describe(nepali_date.today_npt())


@router.get("/convert", response_model=ConvertResult)
def convert(
    ad_date: date | None = Query(default=None, description="AD date to convert to BS"),
    bs_year: int | None = Query(default=None),
    bs_month: int | None = Query(default=None, ge=1, le=12),
    bs_day: int | None = Query(default=None, ge=1, le=32),
) -> ConvertResult:
    try:
        if ad_date is not None:
            return _describe(ad_date)
        if None not in (bs_year, bs_month, bs_day):
            return _describe(nepali_date.bs_to_ad(bs_year, bs_month, bs_day))
    except nepali_date.DateOutOfRange as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    raise HTTPException(
        status_code=422,
        detail="Provide either 'ad_date' or all of 'bs_year', 'bs_month', 'bs_day'",
    )
