from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from dateutil import tz as _tz


_ISO_RE = re.compile(
    r"""
    ^
    (?P<date>\d{4}-\d{2}-\d{2})
    (?:[T\s]
        (?P<time>\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?)
        (?P<tz>
            Z|
            [+-]\d{2}:\d{2}|
            [+-]\d{4}
        )?
    )?
    $
    """,
    re.VERBOSE,
)

_SLASH_YMD_RE = re.compile(
    r"^(?P<y>\d{4})/(?P<m>\d{1,2})/(?P<d>\d{1,2})(?:\s+(?P<t>.*))?$"
)
_SLASH_MDY_RE = re.compile(
    r"^(?P<m>\d{1,2})/(?P<d>\d{1,2})/(?P<y>\d{2,4})(?:\s+(?P<t>.*))?$"
)

_AMPM_TIME_RE = re.compile(
    r"^(?P<h>\d{1,2})(?::(?P<mi>\d{2}))?(?::(?P<s>\d{2}))?\s*(?P<ap>am|pm)$",
    re.IGNORECASE,
)

_TZNAME_RE = re.compile(r"\b(UTC|GMT)\b", re.IGNORECASE)
_TZOFFSET_RE = re.compile(r"(?P<sign>[+-])(?P<h>\d{2}):?(?P<m>\d{2})$")


def _parse_tz_offset(s: str):
    if not s:
        return None
    if s == "Z":
        return timezone.utc
    m = _TZOFFSET_RE.match(s)
    if not m:
        return None
    sign = 1 if m.group("sign") == "+" else -1
    hh = int(m.group("h"))
    mm = int(m.group("m"))
    return timezone(sign * timedelta(hours=hh, minutes=mm))


def _from_iso(s: str) -> datetime | None:
    m = _ISO_RE.match(s.strip())
    if not m:
        return None
    datepart = m.group("date")
    timepart = m.group("time")
    tzpart = m.group("tz")
    if timepart is None:
        # date only
        y, mo, d = map(int, datepart.split("-"))
        return datetime(y, mo, d)
    # time
    # support fractional seconds
    if "." in timepart:
        t_main, frac = timepart.split(".", 1)
        frac = (frac + "000000")[:6]
    else:
        t_main, frac = timepart, "000000"
    pieces = t_main.split(":")
    hh = int(pieces[0])
    mi = int(pieces[1])
    ss = int(pieces[2]) if len(pieces) > 2 else 0
    us = int(frac)
    tzinfo = _parse_tz_offset(tzpart) if tzpart else None
    return datetime(*map(int, datepart.split("-")), hh, mi, ss, us, tzinfo=tzinfo)


def _try_email(s: str) -> datetime | None:
    try:
        dt = parsedate_to_datetime(s)
    except Exception:
        return None
    if dt is None:
        return None
    return dt


def _normalize_spaces(s: str) -> str:
    return " ".join(s.strip().split())


def _parse_named_tz(s: str) -> tuple[str, object | None]:
    # Replace trailing " UTC"/" GMT" with tzinfo=UTC
    m = _TZNAME_RE.search(s)
    if not m:
        return s, None
    name = m.group(1).upper()
    if name in ("UTC", "GMT"):
        # Remove the token (common in "YYYY-mm-dd HH:MM:SS UTC")
        s2 = _TZNAME_RE.sub("", s).strip()
        return s2, _tz.UTC
    return s, None


def _parse_with_formats(s: str, dayfirst: bool = False, yearfirst: bool = False) -> datetime | None:
    # Common formats exercised by tests
    fmts = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y%m%d",
        "%Y%m%dT%H%M%S",
        "%Y%m%d %H%M%S",
        "%b %d %Y %H:%M:%S",
        "%b %d %Y %H:%M",
        "%b %d %Y",
        "%B %d %Y %H:%M:%S",
        "%B %d %Y %H:%M",
        "%B %d %Y",
        "%d %b %Y %H:%M:%S",
        "%d %b %Y %H:%M",
        "%d %b %Y",
        "%d %B %Y %H:%M:%S",
        "%d %B %Y %H:%M",
        "%d %B %Y",
        "%a, %d %b %Y %H:%M:%S",
        "%a, %d %b %Y %H:%M",
    ]
    s = _normalize_spaces(s)
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue

    # slash formats
    m = _SLASH_YMD_RE.match(s)
    if m:
        y, mo, d = int(m.group("y")), int(m.group("m")), int(m.group("d"))
        rest = m.group("t")
        if not rest:
            return datetime(y, mo, d)
        t = _parse_time(rest)
        if t:
            hh, mi, ss, us, tzinfo = t
            return datetime(y, mo, d, hh, mi, ss, us, tzinfo=tzinfo)
    m = _SLASH_MDY_RE.match(s)
    if m:
        mo, d, y = int(m.group("m")), int(m.group("d")), int(m.group("y"))
        if y < 100:
            y += 2000 if y < 69 else 1900
        rest = m.group("t")
        if not rest:
            return datetime(y, mo, d)
        t = _parse_time(rest)
        if t:
            hh, mi, ss, us, tzinfo = t
            return datetime(y, mo, d, hh, mi, ss, us, tzinfo=tzinfo)

    return None


def _parse_time(t: str):
    t = _normalize_spaces(t)
    tzinfo = None

    # allow trailing timezone offset like "-0500" or "-05:00" or "Z"
    tz_m = re.search(r"(Z|[+-]\d{2}:?\d{2})$", t)
    if tz_m:
        tz_str = tz_m.group(1)
        tzinfo = _parse_tz_offset(tz_str)
        t = t[: -len(tz_str)].strip()

    # allow trailing "UTC"/"GMT"
    t, named = _parse_named_tz(t)
    if named is not None:
        tzinfo = named

    # AM/PM
    am = _AMPM_TIME_RE.match(t)
    if am:
        h = int(am.group("h"))
        mi = int(am.group("mi") or 0)
        ss = int(am.group("s") or 0)
        ap = am.group("ap").lower()
        if ap == "pm" and h != 12:
            h += 12
        if ap == "am" and h == 12:
            h = 0
        return h, mi, ss, 0, tzinfo

    # HH:MM[:SS[.ffffff]]
    if re.match(r"^\d{1,2}:\d{2}", t):
        us = 0
        if "." in t:
            left, frac = t.split(".", 1)
            frac = (re.split(r"\s+", frac)[0] + "000000")[:6]
            us = int(frac)
            t = left
        parts = t.split(":")
        h = int(parts[0])
        mi = int(parts[1])
        ss = int(parts[2]) if len(parts) > 2 else 0
        return h, mi, ss, us, tzinfo

    return None


def parse(timestr, default=None, ignoretz=False, tzinfos=None, dayfirst=False, yearfirst=False, fuzzy=False):
    """
    Parse a datetime string into a datetime.datetime.

    This is a small, compatible subset of dateutil.parser.parse supporting:
    - ISO-8601 timestamps with Z or numeric offsets
    - RFC 2822 / email date strings
    - Common human-friendly formats and month names
    - Optional trailing "UTC"/"GMT"
    """
    if isinstance(timestr, datetime):
        dt = timestr
        if ignoretz and dt.tzinfo is not None:
            return dt.replace(tzinfo=None)
        return dt

    if not isinstance(timestr, str):
        raise TypeError("parse() argument must be a string or datetime")

    s = timestr.strip()

    # ISO first
    dt = _from_iso(s)
    if dt is None:
        dt = _try_email(s)
    if dt is None:
        # Handle common "YYYY-mm-ddTHH:MM:SS" without offset by delegating to fromisoformat
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            dt = None
    if dt is None:
        # trailing named tz
        s2, named = _parse_named_tz(s)
        dt = _parse_with_formats(s2, dayfirst=dayfirst, yearfirst=yearfirst)
        if dt is not None and named is not None:
            dt = dt.replace(tzinfo=named)
    if dt is None:
        # try split date + time
        s_norm = _normalize_spaces(s)
        if " " in s_norm:
            dpart, tpart = s_norm.split(" ", 1)
            # parse date only via formats
            ddt = _parse_with_formats(dpart, dayfirst=dayfirst, yearfirst=yearfirst)
            if ddt is not None:
                tt = _parse_time(tpart)
                if tt:
                    hh, mi, ss, us, tzinfo = tt
                    dt = datetime(ddt.year, ddt.month, ddt.day, hh, mi, ss, us, tzinfo=tzinfo)

    if dt is None:
        raise ValueError(f"Unknown string format: {timestr!r}")

    if tzinfos and dt.tzinfo is None:
        # Minimal tzinfos support: if string ends with a token in tzinfos, apply it.
        # (Most tests rely on offsets/Z/UTC rather than tzinfos.)
        for name, tzv in tzinfos.items():
            if re.search(rf"\b{re.escape(name)}\b", s):
                tzinfo = tzv() if callable(tzv) else tzv
                dt = dt.replace(tzinfo=tzinfo)
                break

    if ignoretz and dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)

    if dt.tzinfo is None and default is not None:
        # Fill missing components from default (subset behavior)
        if not isinstance(default, datetime):
            raise TypeError("default must be a datetime")
        dt = dt.replace(
            year=dt.year if dt.year else default.year,
            month=dt.month if dt.month else default.month,
            day=dt.day if dt.day else default.day,
        )

    return dt