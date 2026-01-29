from __future__ import annotations

import sys
from typing import Any


def echo(message: Any = "", nl: bool = True, err: bool = False) -> None:
    stream = sys.stderr if err else sys.stdout
    if message is None:
        message = ""
    if isinstance(message, (bytes, bytearray)):
        try:
            text = message.decode()
        except Exception:
            text = str(message)
    else:
        text = str(message)
    if nl:
        stream.write(text + "\n")
    else:
        stream.write(text)
    stream.flush()


def _normalize_command_name(name: str) -> str:
    return name.replace("_", "-")


def _option_decl_to_dest(decl: str) -> str:
    # "--foo-bar" -> "foo_bar", "-f" -> "f"
    d = decl.lstrip("-")
    d = d.replace("-", "_")
    return d


def _is_optional_annotation(annotation) -> tuple[bool, object]:
    # Returns (is_optional, inner_type)
    try:
        from typing import get_origin, get_args, Union
    except ImportError:  # pragma: no cover
        return False, annotation

    origin = get_origin(annotation)
    if origin is None:
        return False, annotation
    if origin is Union:
        args = get_args(annotation)
        if len(args) == 2 and (args[0] is type(None) or args[1] is type(None)):
            inner = args[1] if args[0] is type(None) else args[0]
            return True, inner
    return False, annotation


def _to_bool(value: str) -> bool:
    v = value.strip().lower()
    if v in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def convert_value(value: str, annotation) -> object:
    if annotation is None or annotation is str:
        return value
    opt, inner = _is_optional_annotation(annotation)
    if opt:
        if value is None:
            return None
        annotation = inner

    if annotation is bool:
        return _to_bool(value)
    if annotation is int:
        return int(value)
    if annotation is float:
        return float(value)
    # Fallback: try call the type
    try:
        return annotation(value)
    except Exception:
        return value


def _first_line(doc: str | None) -> str | None:
    if not doc:
        return None
    doc = doc.strip("\n")
    if not doc.strip():
        return None
    return doc.strip().splitlines()[0].strip()