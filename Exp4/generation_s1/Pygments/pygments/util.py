from __future__ import annotations

from typing import Any, Iterable, List, Optional


class ClassNotFound(Exception):
    pass


class OptionError(Exception):
    pass


def get_bool_opt(options: dict, key: str, default: bool = False) -> bool:
    if options is None:
        return default
    if key not in options:
        return default
    val = options[key]
    if isinstance(val, bool):
        return val
    if val is None:
        return default
    if isinstance(val, (int,)):
        return bool(val)
    if isinstance(val, str):
        v = val.strip().lower()
        if v in ("1", "yes", "y", "true", "on"):
            return True
        if v in ("0", "no", "n", "false", "off"):
            return False
    raise OptionError(f"Invalid boolean option {key}={val!r}")


def get_int_opt(
    options: dict,
    key: str,
    default: int = 0,
    min: Optional[int] = None,
    max: Optional[int] = None,
) -> int:
    if options is None:
        return default
    if key not in options:
        return default
    val = options[key]
    try:
        ival = int(val)
    except Exception as e:
        raise OptionError(f"Invalid integer option {key}={val!r}") from e
    if min is not None and ival < min:
        raise OptionError(f"Option {key} must be >= {min}")
    if max is not None and ival > max:
        raise OptionError(f"Option {key} must be <= {max}")
    return ival


def get_list_opt(options: dict, key: str, default: Optional[Iterable[str]] = None) -> List[str]:
    if options is None or key not in options:
        return list(default) if default is not None else []
    val = options[key]
    if val is None:
        return list(default) if default is not None else []
    if isinstance(val, (list, tuple)):
        return [str(x) for x in val]
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return []
        # split by comma and/or whitespace
        parts = []
        for chunk in s.replace(",", " ").split():
            if chunk:
                parts.append(chunk)
        return parts
    return [str(val)]


def ensure_str(s: Any, encoding: str = "utf-8", errors: str = "strict") -> str:
    if isinstance(s, str):
        return s
    if isinstance(s, bytes):
        return s.decode(encoding, errors)
    if s is None:
        return ""
    return str(s)


def html_escape(s: str) -> str:
    if s is None:
        return ""
    s = ensure_str(s)
    # order matters: escape & first
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )