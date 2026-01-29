from __future__ import annotations

import re
import datetime as _dt
from datetime import tzinfo

try:
    from zoneinfo import ZoneInfo  # type: ignore
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

UTC: tzinfo = _dt.timezone.utc

_OFFSET_RE = re.compile(r"^(?P<sign>[+-])(?P<h>\d{2})(?::?(?P<m>\d{2}))?$")


def local_timezone() -> tzinfo:
    return _dt.datetime.now().astimezone().tzinfo or UTC


def _fixed_offset_from_string(name: str) -> tzinfo:
    if name == "Z":
        return UTC
    m = _OFFSET_RE.match(name)
    if not m:
        raise ValueError(f"Invalid timezone offset string: {name!r}")
    sign = -1 if m.group("sign") == "-" else 1
    hours = int(m.group("h"))
    minutes = int(m.group("m") or "00")
    if hours > 23 or minutes > 59:
        raise ValueError(f"Invalid timezone offset string: {name!r}")
    delta = _dt.timedelta(hours=hours, minutes=minutes) * sign
    return _dt.timezone(delta)


def timezone(name: str | tzinfo | None) -> tzinfo:
    if name is None:
        return local_timezone()

    if isinstance(name, _dt.tzinfo):
        # Best-effort validation that it's tzinfo-like.
        if getattr(name, "utcoffset", None) is None:
            raise TypeError("Invalid tzinfo provided")
        return name

    if not isinstance(name, str):
        raise TypeError("Timezone must be a string, tzinfo, or None")

    key = name.strip()
    if key in ("UTC", "utc", "Z", "z"):
        return UTC

    # Fixed offsets
    if key.startswith(("+", "-")):
        return _fixed_offset_from_string(key)

    # IANA zones
    if ZoneInfo is None:  # pragma: no cover
        raise NotImplementedError("zoneinfo is not available on this Python version")

    return ZoneInfo(key)