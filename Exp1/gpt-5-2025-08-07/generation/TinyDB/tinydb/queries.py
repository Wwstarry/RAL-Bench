import re
from typing import Any, Callable, Iterable, Optional, Tuple, Union


def _get_path(path: Union[str, Tuple[Union[str, int], ...]]) -> Tuple[Union[str, int], ...]:
    if isinstance(path, tuple):
        return path
    if isinstance(path, str):
        parts = []
        for part in path.split("."):
            # Allow array indices via numeric parts
            if part.isdigit():
                parts.append(int(part))
            else:
                parts.append(part)
        return tuple(parts)
    raise TypeError("Path must be a string or tuple")


def _get_value(doc: Any, path: Tuple[Union[str, int], ...]) -> Any:
    current = doc
    for key in path:
        if isinstance(current, dict) and isinstance(key, str):
            if key not in current:
                return None
            current = current[key]
        elif isinstance(current, (list, tuple)) and isinstance(key, int):
            if key < 0 or key >= len(current):
                return None
            current = current[key]
        else:
            return None
    return current


class Query:
    def __init__(self, func: Callable[[dict], bool], description: Optional[str] = None) -> None:
        self._func = func
        self._desc = description or "Query"

    def __call__(self, doc: dict) -> bool:
        return bool(self._func(doc))

    def __and__(self, other: "Query") -> "Query":
        if not isinstance(other, Query):
            return NotImplemented
        return Query(lambda d: self(d) and other(d), f"({self}) AND ({other})")

    def __or__(self, other: "Query") -> "Query":
        if not isinstance(other, Query):
            return NotImplemented
        return Query(lambda d: self(d) or other(d), f"({self}) OR ({other})")

    def __invert__(self) -> "Query":
        return Query(lambda d: not self(d), f"NOT ({self})")

    def __repr__(self) -> str:
        return self._desc

    @staticmethod
    def all() -> "Query":
        return Query(lambda d: True, "ALL")

    @staticmethod
    def test(func: Callable[[dict], bool], description: Optional[str] = None) -> "Query":
        return Query(func, description or "CustomTest")


class Field:
    def __init__(self, path: Union[str, Tuple[Union[str, int], ...]]) -> None:
        self._path = _get_path(path)

    def _repr(self, op: str, value: Any) -> str:
        path_str = ".".join(str(p) for p in self._path)
        return f"{path_str} {op} {value!r}"

    def _make(self, func: Callable[[dict], bool], desc: str) -> Query:
        return Query(func, desc)

    def __eq__(self, other: Any) -> Query:
        return self._make(lambda d: _get_value(d, self._path) == other, self._repr("==", other))

    def __ne__(self, other: Any) -> Query:
        return self._make(lambda d: _get_value(d, self._path) != other, self._repr("!=", other))

    def __lt__(self, other: Any) -> Query:
        return self._make(lambda d: (_get_value(d, self._path) is not None) and (_get_value(d, self._path) < other),
                          self._repr("<", other))

    def __le__(self, other: Any) -> Query:
        return self._make(lambda d: (_get_value(d, self._path) is not None) and (_get_value(d, self._path) <= other),
                          self._repr("<=", other))

    def __gt__(self, other: Any) -> Query:
        return self._make(lambda d: (_get_value(d, self._path) is not None) and (_get_value(d, self._path) > other),
                          self._repr(">", other))

    def __ge__(self, other: Any) -> Query:
        return self._make(lambda d: (_get_value(d, self._path) is not None) and (_get_value(d, self._path) >= other),
                          self._repr(">=", other))

    def one_of(self, values: Iterable[Any]) -> Query:
        values = list(values)
        return self._make(lambda d: _get_value(d, self._path) in values, self._repr("IN", values))

    def any_of(self, values: Iterable[Any]) -> Query:
        # Alias of one_of
        return self.one_of(values)

    def contains(self, value: Any) -> Query:
        # If the field is a list/str, check membership or substring
        def fn(d: dict) -> bool:
            current = _get_value(d, self._path)
            try:
                if isinstance(current, str) and isinstance(value, str):
                    return value in current
                return value in current  # may raise TypeError
            except TypeError:
                return False

        return self._make(fn, self._repr("CONTAINS", value))

    def exists(self) -> Query:
        return self._make(lambda d: _get_value(d, self._path) is not None,
                          f"{'.'.join(str(p) for p in self._path)} EXISTS")

    def matches(self, pattern: Union[str, re.Pattern], flags: int = 0) -> Query:
        regex = re.compile(pattern, flags) if isinstance(pattern, str) else pattern
        return self._make(lambda d: isinstance(_get_value(d, self._path), str) and bool(regex.search(_get_value(d, self._path))),
                          self._repr("MATCHES", regex.pattern if hasattr(regex, "pattern") else str(regex)))

    def test(self, func: Callable[[Any], bool], description: Optional[str] = None) -> Query:
        desc = description or f"TEST({'.'.join(str(p) for p in self._path)})"
        return self._make(lambda d: func(_get_value(d, self._path)), desc)


def where(path: Union[str, Tuple[Union[str, int], ...]]) -> Field:
    return Field(path)