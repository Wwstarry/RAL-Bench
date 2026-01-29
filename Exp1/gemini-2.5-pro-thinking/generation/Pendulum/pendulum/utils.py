# pendulum/utils.py
from __future__ import annotations

import calendar
import datetime as dt


def _add_months(date: dt.datetime, months: int) -> dt.datetime:
    """
    Adds a number of months to a datetime object.
    """
    if not months:
        return date

    year = date.year + (date.month + months - 1) // 12
    month = (date.month + months - 1) % 12 + 1

    day = date.day
    last_day_of_month = calendar.monthrange(year, month)[1]
    if day > last_day_of_month:
        day = last_day_of_month

    return date.replace(year=year, month=month, day=day)