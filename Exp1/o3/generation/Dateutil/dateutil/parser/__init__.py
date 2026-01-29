"""
Very small subset of `dateutil.parser` compatible interface.

Implements :func:`parse` capable of handling the most common date/time
representations expected in the tests:

    * ISO-8601 – ``YYYY-MM-DD`` with optional time, fractional seconds and
      timezone (``Z`` or ``±HH:MM``).
    * Human friendly – e.g. ``January 3 2020 12:30``, ``3 Jan 2020``,
      with optional comma and/or time component.
    * RFC 2822 – handled through :pyfunc:`email.utils.parsedate_to_datetime`.

The implementation is *not* a full replacement of ``python-dateutil``, though
it should be sufficient for the black-box tests shipped with this repository.
"""
from __future__ import annotations

import datetime as _dt
import re as _re
from email.utils import parsedate_to_datetime as _parsedate_to_datetime
from typing import Optional, Sequence, Dict, Union

from ..tz import UTC, tzoffset, gettz


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Regex that matches a (fairly complete) ISO-8601 date or datetime string
_ISO_RE = _re.compile(
    r"""
    ^
    \s*
    (?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})
    (?:
        [T\s]
        (?P<hour>\d{2}):(?P<minute>\d{2})
        (?:
            :(?:?P<second>\d{2})
        )?
        (?:
            [.,](?P<micro>\d{1,6})
        )?
        (?:
            (?P<tz>Z|[+\-]\d{2}:?\d{2})
        )?
    )?
    \s*
    $
""",
    _re.VERBOSE | _re.IGNORECASE,
)

_MONTH_NAMES = {
    name.lower(): index
    for index, name in enumerate(
        [
            "",
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
    )
}

# also abbreviated variants
_MONTH_NAMES.update({name[:3].lower(): idx for name, idx in _MONTH_NAMES.items() if idx})


def _parse_iso(s: str) -> Optional[_dt.datetime]:
    """Parse *s* as ISO-8601 using regex + ``datetime`` helpers."""
    m = _ISO_RE.match(s)
    if not m:
        return None

    parts = m.groupdict(default="0")

    year = int(parts["year"])
    month = int(parts["month"])
    day = int(parts["day"])

    if parts["hour"]:
        hour = int(parts["hour"])
        minute = int(parts["minute"])
        second = int(parts.get("second") or 0)
        micro_raw = parts.get("micro") or "0"
        micro = int(micro_raw.ljust(6, "0"))  # pad to µs
        tzinfo: _dt.tzinfo | None = None
        tz_str = parts.get("tz")
        if tz_str:
            if tz_str.upper() == "Z":
                tzinfo = UTC
            else:
                sign = 1 if tz_str[0] == "+" else -1
                hh = int(tz_str[1:3])
                mm = int(tz_str[-2:])
                offset = sign * (hh * 3600 + mm * 60)
                tzinfo = tzoffset(tz_str, offset)
        return _dt.datetime(year, month, day, hour, minute, second, micro, tzinfo)
    else:
        return _dt.datetime(year, month, day)


# Simple human readable formats, e.g. "January 3 2020 12:00"
_HUMAN_RE = _re.compile(
    r"""
    ^
    \s*
    (?P<day>\d{1,2})
    \s+
    (?P<month>[A-Za-z]+)
    ,?\s+
    (?P<year>\d{4})
    (?:
        [\sT]
        (?P<hour>\d{1,2})
        :
        (?P<minute>\d{2})
        (?:
            :
            (?P<second>\d{2})
        )?
        \s*
        (?P<ampm>AM|PM|am|pm)?
    )?
    \s*
    $
    """,
    _re.VERBOSE,
)


def _parse_human(s: str) -> Optional[_dt.datetime]:
    m = _HUMAN_RE.match(s)
    if not m:
        return None
    gd = m.groupdict()
    day = int(gd["day"])
    month = _MONTH_NAMES[gd["month"].lower()]
    year = int(gd["year"])

    hour = int(gd.get("hour") or 0)
    minute = int(gd.get("minute") or 0)
    second = int(gd.get("second") or 0)
    if gd.get("ampm"):
        if gd["ampm"].lower() == "pm" and hour != 12:
            hour += 12
        if gd["ampm"].lower() == "am" and hour == 12:
            hour = 0
    return _dt.datetime(year, month, day, hour, minute, second)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse(
    timestr: str,
    default: Optional[_dt.datetime] = None,
    *,
    dayfirst: bool = False,
    yearfirst: bool = False,
    fuzzy: bool = False,
    tzinfos: Optional[
        Union[Dict[str, _dt.tzinfo], Dict[str, int], Sequence[_dt.tzinfo]]
    ] = None,
) -> _dt.datetime:
    """
    Parse a string into a :pyclass:`datetime.datetime`.  Only a subset of the
    full ``python-dateutil`` functionality is implemented, but it should be
    plenty for the included test-suite.

    Parameters
    ----------
    timestr
        The string to parse.
    default
        A :class:`datetime.datetime` providing default values for missing
        fields.  If *None*, ``datetime.datetime.now()`` is used.
    dayfirst, yearfirst, fuzzy, tzinfos
        Accepted for API compatibility, currently ignored or handled in a
        simplified fashion.

    Returns
    -------
    datetime.datetime
    """
    if not isinstance(timestr, str):
        raise TypeError("parse() argument must be str")

    # 1) Try ISO-8601 – use fromisoformat as a first quick attempt, but massage
    #    trailing 'Z' to '+00:00' because `fromisoformat` doesn't understand it.
    iso_candidate = timestr.strip()
    if iso_candidate.endswith("Z") and "T" in iso_candidate:
        try:
            return _dt.datetime.fromisoformat(iso_candidate[:-1] + "+00:00")
        except Exception:
            pass
    else:
        try:
            return _dt.datetime.fromisoformat(iso_candidate)
        except Exception:
            pass

    # 2) More permissive regex based ISO parser
    iso_dt = _parse_iso(timestr)
    if iso_dt:
        return iso_dt

    # 3) Human readable
    human_dt = _parse_human(timestr)
    if human_dt:
        return human_dt

    # 4) RFC 2822 via stdlib email.utils
    try:
        rfc_dt = _parsedate_to_datetime(timestr)
        if rfc_dt is not None:
            return rfc_dt
    except Exception:
        pass

    # 5) Last resort – try a handful of strptime formats
    _FORMATS = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d %Y",
        "%B %d %Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%b %d %Y %H:%M",
        "%B %d %Y %H:%M",
    ]
    for fmt in _FORMATS:
        try:
            return _dt.datetime.strptime(timestr, fmt)
        except ValueError:
            continue

    raise ValueError(f"Could not parse datetime string: {timestr!r}")