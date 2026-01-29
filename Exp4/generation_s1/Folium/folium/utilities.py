from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Union


def json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def js_str(s: Any) -> str:
    # Safe JS string literal via JSON
    return json_dumps("" if s is None else str(s))


def normalize_location(location: Any) -> list[float]:
    if location is None:
        return [0.0, 0.0]
    if isinstance(location, (list, tuple)) and len(location) >= 2:
        return [float(location[0]), float(location[1])]
    raise ValueError("location must be a (lat, lon) pair")


def read_geojson(data: Any) -> Union[dict, list]:
    if isinstance(data, (dict, list)):
        return data
    if isinstance(data, (str, bytes)):
        s = data.decode("utf-8") if isinstance(data, bytes) else data
        # If it's a path, read it
        p = Path(s)
        if p.exists() and p.is_file():
            s = p.read_text(encoding="utf-8")
        try:
            return json.loads(s)
        except Exception as e:
            raise ValueError("Invalid GeoJSON input") from e
    # Path-like
    try:
        p = Path(data)
        if p.exists() and p.is_file():
            s = p.read_text(encoding="utf-8")
            return json.loads(s)
    except Exception:
        pass
    raise ValueError("Invalid GeoJSON input")