"""Timezone handling — specifically that offsets follow DST instead of being fixed.

The bug these cover: the calendar window was built from a hardcoded "-07:00"
alongside the zone name "America/Denver". Denver runs at -07:00 only under MST;
under MDT it is -06:00, so windows were an hour out for most of the year.
"""

from datetime import datetime

from localtime import LOCAL_TIMEZONE, day_bounds, local_now, local_tz


def test_summer_and_winter_offsets_differ():
    # The regression in one assertion: a fixed offset makes these equal.
    summer_start, _ = day_bounds("2026-07-15")  # MDT, -06:00
    winter_start, _ = day_bounds("2026-01-15")  # MST, -07:00
    assert summer_start.utcoffset() != winter_start.utcoffset()


def test_mdt_offset_is_minus_six():
    start, _ = day_bounds("2026-07-15")
    assert start.isoformat() == "2026-07-15T00:00:00-06:00"


def test_mst_offset_is_minus_seven():
    start, _ = day_bounds("2026-01-15")
    assert start.isoformat() == "2026-01-15T00:00:00-07:00"


def test_day_bounds_cover_the_whole_local_day():
    start, end = day_bounds("2026-07-15")
    assert start.date() == end.date()
    assert (start.hour, start.minute) == (0, 0)
    assert (end.hour, end.minute) == (23, 59)
    # Both ends sit at the same offset, so the window is exactly one day.
    assert end - start < __import__("datetime").timedelta(days=1)


def test_day_bounds_are_timezone_aware():
    start, end = day_bounds("2026-07-15")
    assert start.tzinfo is not None and end.tzinfo is not None


def test_local_now_is_aware_and_in_the_configured_zone():
    now = local_now()
    assert now.tzinfo is not None
    assert now.utcoffset() == datetime.now(local_tz()).utcoffset()


def test_timezone_is_a_zone_name_not_an_offset():
    # A fixed offset here would reintroduce the bug.
    assert "/" in LOCAL_TIMEZONE
    assert not LOCAL_TIMEZONE.startswith(("+", "-"))
