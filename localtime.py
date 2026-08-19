"""Timezone handling for Agent Adam.

The calendar code previously paired the zone name "America/Denver" with a
hardcoded "-07:00" offset. Denver is UTC-07:00 only under MST; from the second
Sunday in March to the first Sunday in November it is UTC-06:00. Every time
window built from that constant was an hour out for roughly two thirds of the
year, which pushed events near midnight onto the wrong day.

Offsets are derived from the IANA zone here so they follow DST on their own.
"""

import os
from datetime import date as _date
from datetime import datetime
from datetime import time as _time
from zoneinfo import ZoneInfo

# IANA zone name, never a fixed offset.
LOCAL_TIMEZONE = os.getenv("AGENT_ADAM_TIMEZONE", "America/Denver")


def local_tz() -> ZoneInfo:
    return ZoneInfo(LOCAL_TIMEZONE)


def local_now() -> datetime:
    """Timezone-aware 'now' in the configured zone."""
    return datetime.now(local_tz())


def day_bounds(date_str: str) -> tuple[datetime, datetime]:
    """Aware start and end of a calendar day, at whatever offset DST implies."""
    day = _date.fromisoformat(date_str)
    tz = local_tz()
    return (
        datetime.combine(day, _time.min, tzinfo=tz),
        datetime.combine(day, _time.max, tzinfo=tz),
    )
