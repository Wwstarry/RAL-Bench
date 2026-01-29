# -*- coding: utf-8 -*-
"""
VCardLine parsing and serialization.

This module implements a small, robust subset of vCard line parsing:
- NAME;PARAM=VALUE;PARAM2="QUOTED":VALUE
- Multiple param values separated by commas
- Escaping in value using backslash (\\n, \\;, \\, \\,)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple, Union

_PARAM_SPLIT_RE = re.compile(r";")
_NAME_VALUE_SPLIT_RE = re.compile(r":", re.S)


def _unescape_value(val: str) -> str:
    # vCard 3.0 style escaping
    out = []
    i = 0
    while i < len(val):
        ch = val[i]
        if ch == "\\" and i + 1 < len(val):
            nxt = val[i + 1]
            if nxt in ("\\", ";", ",", ":"):
                out.append(nxt)
                i += 2
                continue
            if nxt in ("n", "N"):
                out.append("\n")
                i += 2
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def _escape_value(val: str) -> str:
    return (
        val.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(";", r"\;")
        .replace(",", r"\,")
        .replace(":", r"\:")
    )


def _quote_param(v: str) -> str:
    if any(c in v for c in (';', ':', ',', '"')) or v.strip() != v:
        return '"' + v.replace('"', r"\"") + '"'
    return v


def _split_params(head: str) -> Tuple[str, List[str]]:
    parts = head.split(";")
    name = parts[0].strip()
    return name, parts[1:]


def _parse_param(p: str) -> Tuple[str, List[str]]:
    if "=" in p:
        k, v = p.split("=", 1)
        key = k.strip().upper()
        raw = v.strip()
    else:
        # Bare parameter in vCard 2.1 (TYPE as bare token) - treat as TYPE
        key = "TYPE"
        raw = p.strip()

    vals: List[str] = []
    cur = []
    in_quotes = False
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == '"' and (i == 0 or raw[i - 1] != "\\"):
            in_quotes = not in_quotes
            i += 1
            continue
        if ch == "," and not in_quotes:
            vals.append("".join(cur).strip())
            cur = []
            i += 1
            continue
        if ch == "\\" and i + 1 < len(raw):
            # allow escaping quotes inside quoted values
            nxt = raw[i + 1]
            cur.append(nxt)
            i += 2
            continue
        cur.append(ch)
        i += 1
    if cur or raw.endswith(","):
        vals.append("".join(cur).strip())

    # Strip surrounding quotes if any remained (defensive)
    cleaned: List[str] = []
    for v in vals:
        v = v.strip()
        if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
            v = v[1:-1].replace(r"\"", '"')
        cleaned.append(v)
    return key, cleaned


@dataclass
class VCardLine:
    name: str
    value: str = ""
    params: Dict[str, List[str]] = field(default_factory=dict)

    @classmethod
    def Parse(cls, line: Union[str, bytes]) -> "VCardLine":
        if isinstance(line, bytes):
            s = line.decode("utf-8", "replace")
        else:
            s = str(line)
        s = s.strip("\r\n")

        if ":" in s:
            head, val = s.split(":", 1)
        else:
            head, val = s, ""

        name, raw_params = _split_params(head)
        params: Dict[str, List[str]] = {}
        for p in raw_params:
            if not p:
                continue
            k, vs = _parse_param(p)
            params.setdefault(k, [])
            for v in vs:
                if v and v not in params[k]:
                    params[k].append(v)

        return cls(name=name.upper(), value=_unescape_value(val), params=params)

    def get(self, param: str, default: Optional[Sequence[str]] = None) -> List[str]:
        return list(self.params.get(param.upper(), default or []))

    def set_param(self, key: str, values: Union[str, Sequence[str]]) -> None:
        k = key.upper()
        if isinstance(values, str):
            vs = [values]
        else:
            vs = list(values)
        self.params[k] = vs

    def as_vcardline(self) -> str:
        parts = [self.name.upper()]
        # stable order for tests
        for k in sorted(self.params.keys()):
            vs = self.params[k]
            if not vs:
                continue
            joined = ",".join(_quote_param(v) for v in vs)
            parts.append(f"{k}={joined}")
        head = ";".join(parts)
        return f"{head}:{_escape_value(self.value)}"

    def __str__(self) -> str:
        return self.as_vcardline()