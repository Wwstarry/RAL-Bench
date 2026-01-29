from __future__ import annotations


def maybe_seconds(value):
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return value