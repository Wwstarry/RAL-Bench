"""
VCard line parsing and serialization.

This module provides a minimal VCardLine implementation for vCard 3.0-like
syntax. It handles properties with optional group, parameters, and escaping.
"""

from typing import Dict, List, Optional


_ESCAPE_MAP = {
    "\\": "\\\\",
    "\n": "\\n",
    ";": "\\;",
    ",": "\\,",
}
_UNESCAPE_MAP = {
    "\\n": "\n",
    "\\N": "\n",
    "\\;": ";",
    "\\,": ",",
    "\\\\": "\\",
}


def escape_value(value: str) -> str:
    if value is None:
        return ""
    out = []
    for ch in str(value):
        out.append(_ESCAPE_MAP.get(ch, ch))
    return "".join(out)


def unescape_value(value: str) -> str:
    if value is None:
        return ""
    v = str(value)
    # Replace longest sequences first
    for k, rep in _UNESCAPE_MAP.items():
        v = v.replace(k, rep)
    return v


def unfold_lines(s: str) -> str:
    """
    Unfold folded vCard lines. Folding is done using CRLF followed by space or tab.
    This implementation simply removes newlines followed by spaces/tabs.
    """
    s = str(s)
    lines = s.splitlines()
    unfolded = []
    for line in lines:
        if line and (line[0] == " " or line[0] == "\t"):
            # Continuation of previous line; append without the leading space
            if unfolded:
                unfolded[-1] += line[1:]
            else:
                unfolded.append(line[1:])
        else:
            unfolded.append(line)
    return "\n".join(unfolded)


class VCardLine:
    """
    Represents a single line of a vCard.

    Format examples:
      FN:John Doe
      EMAIL;TYPE=INTERNET,PREF:john@example.com
      item1.EMAIL;TYPE=HOME:john@home.example

    Attributes:
      group: Optional group/prefix before the property name.
      name: Property name (e.g., FN, EMAIL).
      params: Dict of parameter name -> list of values.
      value: The property value.
    """

    def __init__(self,
                 name: str,
                 value: str = "",
                 params: Optional[Dict[str, List[str]]] = None,
                 group: Optional[str] = None):
        if not name:
            raise ValueError("VCardLine requires a property name")
        self.group = group
        self.name = str(name)
        self.params = {}
        if params:
            for k, v in params.items():
                # Normalize param values to list of strings
                if isinstance(v, (list, tuple)):
                    self.params[str(k).upper()] = [str(x) for x in v]
                else:
                    self.params[str(k).upper()] = [str(v)]
        self.value = str(value)

    def __repr__(self):
        return f"VCardLine({self.group!r}, {self.name!r}, {self.params!r}, {self.value!r})"

    def __str__(self):
        return self.to_line()

    @classmethod
    def parse(cls, line: str):
        """
        Parse a single vCard content line into a VCardLine instance.
        """
        if line is None:
            raise ValueError("Cannot parse None")
        line = unfold_lines(str(line).strip())
        # Split into left (group/name/params) and value
        if ":" in line:
            left, value = line.split(":", 1)
        else:
            left, value = line, ""

        group = None
        name_and_params = left

        # Group detection "group.name"
        if "." in name_and_params:
            potential_group, remainder = name_and_params.split(".", 1)
            if potential_group and remainder:
                group = potential_group
                name_and_params = remainder

        # Split name and params
        parts = name_and_params.split(";")
        name = parts[0].strip()
        params = {}

        for p in parts[1:]:
            p = p.strip()
            if not p:
                continue
            if "=" in p:
                k, v = p.split("=", 1)
                k = k.strip().upper()
                # Parameter values may be comma-separated
                vals = [x.strip() for x in v.split(",") if x.strip() != ""]
                params[k] = vals
            else:
                # Boolean/flag-type parameter (e.g., PREF)
                params[p.upper()] = ["true"]

        return cls(name=name, group=group, params=params, value=unescape_value(value))

    def to_line(self) -> str:
        """
        Serialize the VCardLine back to a vCard content line.
        """
        left = ""
        if self.group:
            left += f"{self.group}."
        left += self.name

        # Serialize params sorted by key for stable output
        for k in sorted(self.params.keys()):
            values = self.params[k]
            if values is None or len(values) == 0:
                # Empty param value
                left += f";{k}="
            elif len(values) == 1 and values[0] == "true":
                # Flag parameter
                left += f";{k}"
            else:
                left += f";{k}=" + ",".join(values)

        return f"{left}:{escape_value(self.value)}"

    def get_param(self, name: str) -> Optional[List[str]]:
        return self.params.get(name.upper())

    def set_param(self, name: str, values):
        if isinstance(values, (list, tuple)):
            self.params[str(name).upper()] = [str(v) for v in values]
        else:
            self.params[str(name).upper()] = [str(values)]

    def remove_param(self, name: str):
        self.params.pop(str(name).upper(), None)

    def clone(self):
        return VCardLine(name=self.name, value=self.value, params={k: list(v) for k, v in self.params.items()}, group=self.group)