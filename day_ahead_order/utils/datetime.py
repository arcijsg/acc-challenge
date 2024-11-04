"""
A bag of useful helpers to be sorted out to separate modules in case it grows
either too big or too heterogenic.
"""

import pytz
from datetime import date, datetime, time

from typing import Optional, Tuple

# from pandas import date_range, DatetimeIndex

# TODO: should we allow to override it via ENV variable?
default_timezone = "Europe/Amsterdam"


def get_prediction_range(
    day: date, tzone=default_timezone
) -> Tuple[datetime, datetime]:
    """
    Args:
        day: (naive) calendar day, as experienced in assumed time zone
        tzone: by default, Amsterdam time - as product scoped for Dutch market
    Returns:
        Pandas DatetimeIndex with two items that spans a full day
        in the provided timezone
        (depending on daylight saving status on given day, it spans over
        23, 24 or 25 hours).

        The end of the range is exclusive (beginning of the first second of the next day)
    """
    # With Pandas, a simpler way is possible, but at least HistoricConsumptionService
    # treats the end of the day as inclusive and adds another 15-minute period
    # to requested results:
    # calendar_day = datetime.combine(day, time.min)
    # return date_range(start=calendar_day, freq="D", periods=2, tz=tzone)
    assumed_tz = pytz.timezone(tzone)

    begins = assumed_tz.localize(datetime.combine(day, time.min))
    ends = assumed_tz.localize(datetime.combine(day, time.max))

    return (begins.astimezone(pytz.utc), ends.astimezone(pytz.utc))


def last_weekday_before(weekday: int, anchor: Optional[date] = None) -> date:
    """
    Args:
        weekday: 0 (Monday) to 6 (Sunday)
        anchor: (naive calendar) date before which to look (defaults to today)
    """
    if weekday not in range(7):
        raise ValueError("weekday should be 0..6 (Mon to Sun)")

    if anchor is None:
        anchor = date.today()

    offset = (anchor.weekday() - weekday) % 7
    # If anchor date (e.g., today) happens to be the weekday of interest, get
    # one from previous week instead.
    if offset == 0:
        offset = 7
    return anchor - timedelta(days=offset)
