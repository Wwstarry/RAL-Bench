from __future__ import annotations

from datetime import datetime as _dt


def format_datetime_iso(dt: _dt) -> str:
    # Pendulum usually emits ISO8601 with offset.
    # stdlib dt.isoformat() is close; ensure seconds and microseconds preserved.
    return dt.isoformat()