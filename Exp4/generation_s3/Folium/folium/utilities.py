from __future__ import annotations

import html
import json
import itertools
from collections.abc import Sequence

_id_counter = itertools.count(1)


def generate_id(prefix: str = "") -> str:
    # Deterministic per-process incrementing ids.
    n = next(_id_counter)
    if prefix:
        return f"{prefix}{n}"
    return str(n)


def to_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def escape_html(s: str) -> str:
    return html.escape(s, quote=True)


def validate_location(location) -> list[float]:
    if location is None:
        raise ValueError("location must be a 2-sequence of numbers, got None")
    if isinstance(location, (str, bytes)):
        raise TypeError("location must be a 2-sequence of numbers")
    if not isinstance(location, Sequence) or len(location) != 2:
        raise ValueError("location must be a 2-sequence of numbers")
    lat, lon = location[0], location[1]
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except Exception as e:
        raise ValueError("location must contain numeric values") from e
    return [lat_f, lon_f]


def js_var_name(prefix: str, element_id: str) -> str:
    # Leaflet/JS-friendly variable name.
    safe_prefix = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in prefix).lower()
    return f"{safe_prefix}_{element_id}"