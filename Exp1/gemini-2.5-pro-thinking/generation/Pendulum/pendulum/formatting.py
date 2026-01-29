# pendulum/formatting.py
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone as dt_timezone

from .datetime import DateTime
from .timezone import Timezone, timezone as get_timezone, UTC

# A more robust ISO 8601 regex
# Handles date, time (with T or space), optional fractional seconds, and timezone (Z, +-hh:mm, +-hhmm, +-hh)
ISO8601_REGEX = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})"
    r"([T ]"
    r"(?P<time>\d{2}:\d{2}:\d{2})"
    r"(?P<frac>\.\d{1,6})?\d*"  # Allow more than 6 digits but only parse 6
    r")?"
    r"(?P<tz>"
    r"Z|[+-]\d{2}(:?\d{2})?"
    r")?$"
)


def parse(text: str, *, tz: str | Timezone | None = None) -> DateTime:
    """
    Parses a string into a DateTime instance.
    """
    match = ISO8601_REGEX.match(text)
    if not match:
        # Fallback for other common formats if needed, but for now, raise error
        raise ValueError(f"Unable to parse string '{text}'")

    groups = match.groupdict()

    dt_str = groups["date"]
    if groups["time"]:
        dt_str += "T" + groups["time"]
    else:
        # If no time is present, it's a date string. Default to midnight.
        dt_str += "T00:00:00"

    if groups["frac"]:
        # Ensure microseconds are exactly 6 digits for fromisoformat
        dt_str += groups["frac"][:7]

    dt = datetime.fromisoformat(dt_str)

    tz_info = None
    if groups["tz"]:
        tz_str = groups["tz"]
        if tz_str.upper() == "Z":
            tz_info = UTC
        else:
            sign = -1 if tz_str[0] == "-" else 1
            tz_str = tz_str[1:]
            if ":" in tz_str:
                hours, minutes = map(int, tz_str.split(":"))
            elif len(tz_str) == 4:
                hours, minutes = int(tz_str[:2]), int(tz_str[2:])
            else:
                hours, minutes = int(tz_str), 0

            offset = timedelta(hours=hours, minutes=minutes) * sign
            tz_info = dt_timezone(offset)
    elif tz:
        if isinstance(tz, str):
            tz_info = get_timezone(tz)
        else:
            tz_info = tz

    if tz_info:
        dt = dt.replace(tzinfo=tz_info)

    return DateTime(
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second,
        dt.microsecond,
        tzinfo=dt.tzinfo,
    )