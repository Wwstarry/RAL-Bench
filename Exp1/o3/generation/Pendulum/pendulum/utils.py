from __future__ import annotations

from datetime import datetime as _dt
from datetime import timedelta as _td
from datetime import timezone as _tz

from typing import Any

###############################################################
# Misc. helpers used across the tiny codebase
###############################################################


def _make_datetime_kwargs(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
    microsecond: int,
    tz: str | int | float | None,
) -> dict[str, Any]:
    from .timezone import timezone

    tzinfo = timezone(tz) if tz is not None else None

    return dict(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        second=second,
        microsecond=microsecond,
        tzinfo=tzinfo,
    )


def _total_seconds(td: _td) -> float:
    """
    Back-port of :pymeth:`datetime.timedelta.total_seconds` for Py3.7.  (It does
    exist there but an explicit helper makes typing/coverage easier.)
    """
    return td.days * 24 * 3600 + td.seconds + td.microseconds / 1_000_000.0