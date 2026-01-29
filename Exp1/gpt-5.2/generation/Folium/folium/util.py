from __future__ import annotations

import json
import re
import uuid
from typing import Any


_JS_UNSAFE = re.compile(r"[^\w]")


def get_name(prefix: str = "id") -> str:
    """Create a reasonably unique, JS-safe variable name."""
    u = uuid.uuid4().hex
    return f"{prefix}_{u}"


def js_var(name: str) -> str:
    """Coerce a name into a JS variable-ish token (best effort)."""
    if not name:
        return get_name("var")
    n = _JS_UNSAFE.sub("_", name)
    if n[0].isdigit():
        n = "_" + n
    return n


def tojson(obj: Any) -> str:
    """JSON dump with stable output and JS-friendly primitives."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )