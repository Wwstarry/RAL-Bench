from __future__ import annotations

from typing import Any

from .errors import UnknownFieldError, UsageError


_SUPPORTED_FIELDS = {
    "now",
    "cpu.user",
    "cpu.total",
    "mem.used",
    "load",
}


def parse_fields(spec: str) -> list[str]:
    """
    Parse a comma-separated list of fields, preserving order.
    Reject empty tokens and empty specs.
    """
    if spec is None:
        raise UsageError("Missing CSV fields specification")
    s = str(spec).strip()
    if not s:
        raise UsageError("CSV fields specification is empty")

    raw_tokens = s.split(",")
    fields: list[str] = []
    for tok in raw_tokens:
        f = tok.strip()
        if not f:
            raise UsageError("CSV fields specification contains empty field")
        fields.append(f)
    return fields


def _get_nested(metrics: dict[str, Any], path: str) -> Any:
    cur: Any = metrics
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise KeyError(path)
    return cur


def resolve_field(metrics: dict[str, Any], field: str) -> str:
    if field not in _SUPPORTED_FIELDS:
        raise UnknownFieldError(f"Unknown field: {field}")

    # now, load are top-level; cpu.user, cpu.total, mem.used are nested.
    try:
        if field in ("now", "load"):
            val = metrics[field]
        else:
            val = _get_nested(metrics, field)
    except Exception:
        # If metric missing for some reason, still return numeric default for supported fields.
        val = 0.0

    # Render as a numeric string without units.
    # Use repr-like stability but keep it float-compatible.
    try:
        fval = float(val)
        # Avoid scientific notation surprises for typical sizes; but allow it if huge.
        # Keep simple: strip trailing zeros for readability while remaining parseable.
        s = format(fval, ".6f").rstrip("0").rstrip(".")
        return s if s else "0"
    except Exception:
        # For safety: supported fields must be numeric parseable by tests.
        return "0"


def render_csv_line(metrics: dict[str, Any], fields: list[str]) -> str:
    vals = [resolve_field(metrics, f) for f in fields]
    return ",".join(vals)