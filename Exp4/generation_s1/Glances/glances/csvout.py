from __future__ import annotations

from typing import List

from .errors import UnknownFieldError, UsageError
from .metrics import get_snapshot

ALLOWED_FIELDS = {"now", "cpu.user", "cpu.total", "mem.used", "load"}


def parse_fields(spec: str) -> List[str]:
    if spec is None:
        raise UsageError("Missing CSV field specification.")
    s = str(spec).strip()
    if not s:
        raise UsageError("Empty CSV field specification.")
    parts = [p.strip() for p in s.split(",")]
    if any(p == "" for p in parts):
        raise UsageError("CSV field specification contains empty field name.")
    return parts


def validate_fields(fields: List[str]) -> None:
    unknown = [f for f in fields if f not in ALLOWED_FIELDS]
    if unknown:
        raise UnknownFieldError("Unknown CSV field(s): " + ", ".join(unknown))


def collect_row(fields: List[str]) -> List[str]:
    validate_fields(fields)
    snap = get_snapshot()
    values = []
    for f in fields:
        v = snap.get(f, 0)
        values.append(str(v))
    return values


def format_csv_row(values: List[str]) -> str:
    # Values are numeric; minimal formatting (no quoting) is sufficient.
    return ",".join(values)