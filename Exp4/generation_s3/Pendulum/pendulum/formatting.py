from __future__ import annotations

import datetime as _dt

from .timezone import UTC


def _offset_colon(dt: _dt.datetime) -> str:
    off = dt.utcoffset()
    if off is None:
        return ""
    total = int(off.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    hh = total // 3600
    mm = (total % 3600) // 60
    return f"{sign}{hh:02d}:{mm:02d}"


def _offset_nocolon_or_z(dt: _dt.datetime) -> str:
    off = dt.utcoffset()
    if off is None:
        return ""
    if off == _dt.timedelta(0):
        return "Z"
    total = int(off.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    hh = total // 3600
    mm = (total % 3600) // 60
    return f"{sign}{hh:02d}{mm:02d}"


def to_iso8601(dt: _dt.datetime) -> str:
    # We build this ourselves to ensure consistent offset formatting.
    date_part = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"
    time_part = f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"
    if dt.microsecond:
        time_part += f".{dt.microsecond:06d}"

    if dt.tzinfo is None or dt.utcoffset() is None:
        return f"{date_part}T{time_part}"

    return f"{date_part}T{time_part}{_offset_colon(dt)}"


def format_datetime(dt: _dt.datetime, fmt: str) -> str:
    # If user provided strftime directives, just use them.
    if "%" in fmt:
        return dt.strftime(fmt)

    # Minimal Pendulum-like token replacement.
    out = fmt

    # Replace longer tokens first to avoid partial overlaps.
    replacements = {
        "SSSSSS": f"{dt.microsecond:06d}",
        "YYYY": f"{dt.year:04d}",
        "MM": f"{dt.month:02d}",
        "DD": f"{dt.day:02d}",
        "HH": f"{dt.hour:02d}",
        "mm": f"{dt.minute:02d}",
        "ss": f"{dt.second:02d}",
    }

    for k in sorted(replacements.keys(), key=len, reverse=True):
        out = out.replace(k, replacements[k])

    # Timezone tokens
    if "ZZ" in out:
        out = out.replace("ZZ", _offset_colon(dt))
    if "Z" in out:
        # "Z" token: prefer +HHMM or 'Z' for UTC.
        out = out.replace("Z", _offset_nocolon_or_z(dt))

    return out