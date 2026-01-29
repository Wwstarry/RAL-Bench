from __future__ import annotations

import json
import typing as t

NoneType = type(None)


def is_optional(tp: t.Any) -> bool:
    origin = t.get_origin(tp)
    if origin is t.Union:
        args = t.get_args(tp)
        return any(a is NoneType for a in args)
    return False


def optional_inner(tp: t.Any) -> t.Any:
    origin = t.get_origin(tp)
    if origin is t.Union:
        args = tuple(a for a in t.get_args(tp) if a is not NoneType)
        if len(args) == 1:
            return args[0]
    return tp


def to_jsonable(obj: t.Any) -> t.Any:
    if hasattr(obj, "dict") and callable(obj.dict):
        return obj.dict()
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(v) for v in obj]
    return obj


def json_dumps(data: t.Any, **kwargs: t.Any) -> str:
    default = kwargs.pop("default", None)

    def _default(x: t.Any) -> t.Any:
        if default is not None:
            return default(x)
        return to_jsonable(x)

    return json.dumps(data, default=_default, **kwargs)