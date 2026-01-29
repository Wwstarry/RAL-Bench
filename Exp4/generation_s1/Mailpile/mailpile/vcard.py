from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

from mailpile.util import safe_str


def unescape_value(value: str) -> str:
    """
    Unescape vCard value escapes:
      \\n or \\N -> newline
      \\, -> comma
      \\; -> semicolon
      \\\\ -> backslash
    """
    # Do a small state machine to avoid double-unescaping surprises.
    out = []
    i = 0
    while i < len(value):
        ch = value[i]
        if ch != "\\":
            out.append(ch)
            i += 1
            continue
        # Escape sequence
        i += 1
        if i >= len(value):
            out.append("\\")
            break
        esc = value[i]
        if esc in ("n", "N"):
            out.append("\n")
        elif esc == ",":
            out.append(",")
        elif esc == ";":
            out.append(";")
        elif esc == "\\":
            out.append("\\")
        else:
            # Unknown escape; keep as-is (backslash removed per common behavior)
            out.append(esc)
        i += 1
    return "".join(out)


def escape_value(value: str) -> str:
    """
    Escape vCard value:
      backslash first, then newlines, comma, semicolon.
    """
    v = value.replace("\\", "\\\\")
    v = v.replace("\r\n", "\n").replace("\r", "\n")
    v = v.replace("\n", "\\n")
    v = v.replace(",", "\\,")
    v = v.replace(";", "\\;")
    return v


def _split_group_and_name(name_part: str) -> Tuple[Optional[str], str]:
    if "." in name_part:
        grp, nm = name_part.split(".", 1)
        return grp, nm
    return None, name_part


def parse_params(chunks: List[str]) -> Dict[str, List[str]]:
    params: Dict[str, List[str]] = {}
    for chunk in chunks:
        if not chunk:
            continue
        if "=" in chunk:
            k, v = chunk.split("=", 1)
            key = safe_str(k).strip().upper()
            val = safe_str(v).strip()
            if val == "":
                vals = [""]
            else:
                vals = [p for p in val.split(",")]
            params[key] = vals
        else:
            # Bare parameter; represent as key with empty value list
            key = safe_str(chunk).strip().upper()
            if key:
                params[key] = []
    return params


@dataclass
class VCardLine:
    name: Optional[str] = None
    value: Optional[str] = None
    params: Optional[Dict[str, List[str]]] = None
    group: Optional[str] = None

    def __post_init__(self) -> None:
        if self.name is not None:
            self.name = safe_str(self.name).strip().upper()
        if self.group is not None:
            self.group = safe_str(self.group).strip()
        if self.value is None:
            self.value = ""
        else:
            self.value = safe_str(self.value)
        if self.params is None:
            self.params = {}
        else:
            # Normalize keys to uppercase and values to lists of strings
            norm: Dict[str, List[str]] = {}
            for k, v in self.params.items():
                kk = safe_str(k).strip().upper()
                if v is None:
                    norm[kk] = []
                elif isinstance(v, (list, tuple)):
                    norm[kk] = [safe_str(x) for x in v]
                else:
                    norm[kk] = [safe_str(v)]
            self.params = norm

    @classmethod
    def Parse(cls, line: Any) -> "VCardLine":
        s = safe_str(line).rstrip("\r\n")

        if ":" in s:
            left, raw_value = s.split(":", 1)
        else:
            left, raw_value = s, ""

        left_parts = left.split(";")
        name_part = left_parts[0].strip()
        group, name = _split_group_and_name(name_part)
        params = parse_params([p.strip() for p in left_parts[1:]])

        value = unescape_value(raw_value)
        return cls(name=name, value=value, params=params, group=group)

    def as_vcardline(self) -> str:
        name = (self.name or "").strip().upper()
        if self.group:
            prefix = f"{self.group}.{name}"
        else:
            prefix = name

        # Stable/deterministic output: sort param keys
        pbits: List[str] = []
        for key in sorted((self.params or {}).keys()):
            vals = (self.params or {}).get(key, [])
            if vals is None:
                vals = []
            if len(vals) == 0:
                pbits.append(key)
            else:
                pbits.append(f"{key}=" + ",".join(safe_str(v) for v in vals))

        escaped = escape_value(safe_str(self.value))
        if pbits:
            return prefix + ";" + ";".join(pbits) + ":" + escaped
        return prefix + ":" + escaped

    def __str__(self) -> str:
        return self.as_vcardline()

    def __repr__(self) -> str:
        return f"VCardLine(group={self.group!r}, name={self.name!r}, params={self.params!r}, value={self.value!r})"

    def get(self, param_name: str, default=None):
        if not self.params:
            return default
        key = safe_str(param_name).strip().upper()
        return self.params.get(key, default)