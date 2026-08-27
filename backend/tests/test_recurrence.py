from datetime import date

from app import nepali_date as nd
from app.models import Event
from app.recurrence import next_occurrence, occurrences_in_range


def make_event(**kw) -> Event:
    defaults = dict(
        title="x",
        description="",
        ad_date=date(2025, 1, 1),
        bs_year=2081,
        bs_month=9,
        bs_day=17,
        category="personal",
        is_holiday=False,
        recurrence="none",
        notify_days_before=1,
        notify_enabled=True,
        source="user",
    )
    defaults.update(kw)
    return Event(**defaults)


def test_none_only_fires_on_its_date():
    e = make_event(ad_date=date(2025, 6, 10), recurrence="none")
    assert occurrences_in_range(e, date(2025, 1, 1), date(2025, 12, 31)) == [date(2025, 6, 10)]
    assert occurrences_in_range(e, date(2026, 1, 1), date(2026, 12, 31)) == []


def test_yearly_ad_one_per_year():
    e = make_event(ad_date=date(2000, 3, 15), recurrence="yearly_ad")
    occ = occurrences_in_range(e, date(2025, 1, 1), date(2027, 12, 31))
    assert occ == [date(2025, 3, 15), date(2026, 3, 15), date(2027, 3, 15)]


def test_yearly_ad_handles_leap_day():
    e = make_event(ad_date=date(2020, 2, 29), recurrence="yearly_ad")
    occ = occurrences_in_range(e, date(2025, 1, 1), date(2025, 12, 31))
    assert occ == [date(2025, 2, 28)]


def test_yearly_bs_same_bs_day_each_year():
    # Nepali New Year: Baishakh 1
    e = make_event(recurrence="yearly_bs", bs_month=1, bs_day=1)
    occ = occurrences_in_range(e, date(2025, 1, 1), date(2027, 12, 31))
    assert len(occ) >= 2
    for d in occ:
        b = nd.ad_to_bs(d)
        assert (b.month, b.day) == (1, 1)


def test_next_occurrence_skips_past():
    e = make_event(ad_date=date(2020, 1, 1), recurrence="none")
    assert next_occurrence(e, date(2025, 1, 1)) is None

    e2 = make_event(ad_date=date(2000, 12, 25), recurrence="yearly_ad")
    nxt = next_occurrence(e2, date(2025, 6, 1))
    assert nxt == date(2025, 12, 25)
