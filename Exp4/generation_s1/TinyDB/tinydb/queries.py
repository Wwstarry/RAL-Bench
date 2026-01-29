from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Sequence, Tuple, Union


def _resolve_path(doc: Any, path: Sequence[Any]) -> Tuple[bool, Any]:
    cur = doc
    for key in path:
        if isinstance(cur, dict):
            if key in cur:
                cur = cur[key]
            else:
                return False, None
        elif isinstance(cur, (list, tuple)) and isinstance(key, int):
            if 0 <= key < len(cur):
                cur = cur[key]
            else:
                return False, None
        else:
            return False, None
    return True, cur


@dataclass(frozen=True)
class QueryInstance:
    _predicate: Callable[[dict], bool]

    def __call__(self, doc: dict) -> bool:
        try:
            return bool(self._predicate(doc))
        except Exception:
            return False

    def __and__(self, other: "QueryInstance") -> "QueryInstance":
        return QueryInstance(lambda doc: self(doc) and other(doc))

    def __or__(self, other: "QueryInstance") -> "QueryInstance":
        return QueryInstance(lambda doc: self(doc) or other(doc))

    def __invert__(self) -> "QueryInstance":
        return QueryInstance(lambda doc: not self(doc))


class Query:
    def __init__(self, path: Tuple[Any, ...] = ()):
        self._path = path

    def __getattr__(self, item: str) -> "Query":
        if item.startswith("_"):
            raise AttributeError(item)
        return Query(self._path + (item,))

    def __getitem__(self, item: Any) -> "Query":
        return Query(self._path + (item,))

    def exists(self) -> QueryInstance:
        path = self._path
        return QueryInstance(lambda doc: _resolve_path(doc, path)[0])

    def equals(self, value: Any) -> QueryInstance:
        path = self._path
        def pred(doc: dict) -> bool:
            ok, v = _resolve_path(doc, path)
            return ok and v == value
        return QueryInstance(pred)

    def not_equals(self, value: Any) -> QueryInstance:
        path = self._path
        def pred(doc: dict) -> bool:
            ok, v = _resolve_path(doc, path)
            return ok and v != value
        return QueryInstance(pred)

    def one_of(self, values: Iterable[Any]) -> QueryInstance:
        s = set(values)
        path = self._path
        def pred(doc: dict) -> bool:
            ok, v = _resolve_path(doc, path)
            return ok and v in s
        return QueryInstance(pred)

    def matches(self, regex_or_pattern: Union[str, "re.Pattern[str]"]) -> QueryInstance:
        pat = re.compile(regex_or_pattern) if isinstance(regex_or_pattern, str) else regex_or_pattern
        path = self._path
        def pred(doc: dict) -> bool:
            ok, v = _resolve_path(doc, path)
            if not ok:
                return False
            return pat.search(str(v)) is not None
        return QueryInstance(pred)

    def test(self, fn: Callable[[Any], bool]) -> QueryInstance:
        path = self._path
        def pred(doc: dict) -> bool:
            ok, v = _resolve_path(doc, path)
            return ok and bool(fn(v))
        return QueryInstance(pred)

    def any(self, fn_or_query: Union[Callable[[Any], bool], QueryInstance]) -> QueryInstance:
        path = self._path
        def pred(doc: dict) -> bool:
            ok, v = _resolve_path(doc, path)
            if not ok or not isinstance(v, list):
                return False
            if isinstance(fn_or_query, QueryInstance):
                return any(fn_or_query(item) if isinstance(item, dict) else False for item in v)
            return any(bool(fn_or_query(item)) for item in v)
        return QueryInstance(pred)

    def all(self, fn_or_query: Union[Callable[[Any], bool], QueryInstance]) -> QueryInstance:
        path = self._path
        def pred(doc: dict) -> bool:
            ok, v = _resolve_path(doc, path)
            if not ok or not isinstance(v, list):
                return False
            if isinstance(fn_or_query, QueryInstance):
                return all(fn_or_query(item) if isinstance(item, dict) else False for item in v)
            return all(bool(fn_or_query(item)) for item in v)
        return QueryInstance(pred)

    def __eq__(self, value: Any) -> QueryInstance:  # type: ignore[override]
        return self.equals(value)

    def __ne__(self, value: Any) -> QueryInstance:  # type: ignore[override]
        return self.not_equals(value)

    def _cmp(self, op: Callable[[Any, Any], bool], other: Any) -> QueryInstance:
        path = self._path
        def pred(doc: dict) -> bool:
            ok, v = _resolve_path(doc, path)
            if not ok:
                return False
            try:
                return bool(op(v, other))
            except TypeError:
                return False
        return QueryInstance(pred)

    def __lt__(self, other: Any) -> QueryInstance:
        return self._cmp(lambda a, b: a < b, other)

    def __le__(self, other: Any) -> QueryInstance:
        return self._cmp(lambda a, b: a <= b, other)

    def __gt__(self, other: Any) -> QueryInstance:
        return self._cmp(lambda a, b: a > b, other)

    def __ge__(self, other: Any) -> QueryInstance:
        return self._cmp(lambda a, b: a >= b, other)


def where(key: str) -> Query:
    return Query((key,))