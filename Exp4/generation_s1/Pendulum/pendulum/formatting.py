from __future__ import annotations

import math


def _plural(n: int, unit: str) -> str:
    if n == 1:
        return f"1 {unit}"
    return f"{n} {unit}s"


def _phrase(value: int, unit: str) -> str:
    if unit == "second":
        return "a few seconds"
    if unit == "minute":
        return "a minute" if value == 1 else _plural(value, "minute")
    if unit == "hour":
        return "an hour" if value == 1 else _plural(value, "hour")
    if unit == "day":
        return "a day" if value == 1 else _plural(value, "day")
    if unit == "month":
        return "a month" if value == 1 else _plural(value, "month")
    if unit == "year":
        return "a year" if value == 1 else _plural(value, "year")
    return _plural(value, unit)


def diff_for_humans_from_seconds(
    delta_seconds: float,
    *,
    absolute: bool = False,
    suffix: bool = True,
) -> str:
    is_future = delta_seconds > 0
    seconds = abs(delta_seconds)

    if seconds < 45:
        core = _phrase(0, "second")
    elif seconds < 90:
        core = _phrase(1, "minute")
    elif seconds < 45 * 60:
        core = _phrase(int(round(seconds / 60.0)), "minute")
    elif seconds < 90 * 60:
        core = _phrase(1, "hour")
    elif seconds < 22 * 3600:
        core = _phrase(int(round(seconds / 3600.0)), "hour")
    elif seconds < 36 * 3600:
        core = _phrase(1, "day")
    elif seconds < 26 * 86400:
        core = _phrase(int(round(seconds / 86400.0)), "day")
    elif seconds < 45 * 86400:
        core = _phrase(1, "month")
    elif seconds < 320 * 86400:
        core = _phrase(int(round(seconds / (30.0 * 86400.0))), "month")
    elif seconds < 548 * 86400:
        core = _phrase(1, "year")
    else:
        core = _phrase(int(round(seconds / (365.0 * 86400.0))), "year")

    if absolute or not suffix:
        return core

    if is_future:
        return f"in {core}"
    return f"{core} ago"