from datetime import date

import pytest

from app import nepali_date as nd


@pytest.mark.parametrize(
    "d",
    [
        date(2024, 1, 1),
        date(2025, 4, 14),
        date(2025, 8, 27),
        date(2026, 2, 15),
        date(2027, 12, 31),
    ],
)
def test_round_trip_ad_bs_ad(d):
    b = nd.ad_to_bs(d)
    assert nd.bs_to_ad(b.year, b.month, b.day) == d


def test_days_in_month_range_and_year_length():
    for year in (2081, 2082, 2083):
        lengths = [nd.days_in_bs_month(year, m) for m in range(1, 13)]
        assert all(29 <= n <= 32 for n in lengths)
        assert sum(lengths) in (365, 366)


def test_weekday_sunday_is_zero():
    # 2025-08-24 is a Sunday
    assert nd.bs_weekday(date(2025, 8, 24)) == 0
    assert nd.bs_weekday(date(2025, 8, 30)) == 6  # Saturday


def test_nepali_digits():
    assert nd.to_nepali_digits(2082) == "२०८२"
    assert nd.to_nepali_digits("12-5") == "१२-५"


def test_shift_bs_month_wraps():
    assert nd.shift_bs_month(2082, 1, -1) == (2081, 12)
    assert nd.shift_bs_month(2082, 12, 1) == (2083, 1)
    assert nd.shift_bs_month(2082, 6, 0) == (2082, 6)


def test_month_range_matches_length():
    start, end = nd.bs_month_range_ad(2082, 5)
    assert (end - start).days + 1 == nd.days_in_bs_month(2082, 5)
    assert nd.ad_to_bs(start).day == 1


def test_today_bs_is_plausible():
    assert 2080 <= nd.today_bs().year <= 2100
