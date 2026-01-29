import re
from typing import Dict, List, Optional, Tuple


def _unescape_value(val: str) -> str:
    # vCard escaping (subset sufficient for tests)
    return (
        val.replace(r"\n", "\n")
        .replace(r"\N", "\n")
        .replace(r"\,", ",")
        .replace(r"\;", ";")
        .replace(r"\\", "\\")
    )


def _escape_value(val: str) -> str:
    val = val.replace("\\", r"\\")
    val = val.replace("\n", r"\n")
    val = val.replace(",", r"\,")
    val = val.replace(";", r"\;")
    return val


_PARAM_SPLIT_RE = re.compile(r";(?=(?:[^"]*"[^"]*")*[^"]*$)")


class VCardLine:
    """
    Parse and serialize a single vCard content line.

    Supported format:
      NAME;PARAM=VALUE;PARAM2=V1,V2:VALUE
    """

    def __init__(
        self,
        name: str,
        value: str = "",
        params: Optional[Dict[str, List[str]]] = None,
        group: Optional[str] = None,
    ):
        self.group = group
        self.name = (name or "").upper()
        self.params: Dict[str, List[str]] = {}
        if params:
            for k, v in params.items():
                self.params[k.upper()] = list(v)
        self.value = value

    @classmethod
    def parse(cls, line: str) -> "VCardLine":
        if isinstance(line, bytes):
            line = line.decode("utf-8", "replace")
        line = line.strip("\r\n")
        if ":" not in line:
            raise ValueError("Invalid vCard line (missing ':'): %r" % line)
        left, value = line.split(":", 1)

        group = None
        if "." in left:
            group, left = left.split(".", 1)

        parts = _PARAM_SPLIT_RE.split(left)
        name = parts[0]
        params: Dict[str, List[str]] = {}
        for p in parts[1:]:
            if not p:
                continue
            if "=" in p:
                k, v = p.split("=", 1)
                k = k.strip().upper()
                v = v.strip()
                # Remove surrounding quotes; keep simple
                if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
                    v = v[1:-1]
                vals = [x for x in v.split(",") if x != ""]
                params[k] = vals
            else:
                # "TYPE" shorthand (RFC allows bare parameter values)
                params.setdefault("TYPE", []).append(p.strip())
        return cls(name=name, value=_unescape_value(value), params=params, group=group)

    def as_vcardline(self) -> str:
        left = self.name
        if self.group:
            left = f"{self.group}.{left}"

        # Stable order: TYPE first, then others sorted
        items: List[Tuple[str, List[str]]] = []
        if "TYPE" in self.params:
            items.append(("TYPE", self.params["TYPE"]))
        for k in sorted(k for k in self.params.keys() if k != "TYPE"):
            items.append((k, self.params[k])

                         )
        for k, vals in items:
            if vals is None:
                continue
            if len(vals) == 0:
                left += f";{k}="
            else:
                left += f";{k}=" + ",".join(vals)
        return left + ":" + _escape_value(self.value)

    def __str__(self) -> str:
        return self.as_vcardline()

    def get_param(self, key: str, default=None):
        key = (key or "").upper()
        if key not in self.params:
            return default
        return self.params[key]

    def set_param(self, key: str, values):
        key = (key or "").upper()
        if values is None:
            self.params.pop(key, None)
        elif isinstance(values, (list, tuple)):
            self.params[key] = [str(v) for v in values]
        else:
            self.params[key] = [str(values)]