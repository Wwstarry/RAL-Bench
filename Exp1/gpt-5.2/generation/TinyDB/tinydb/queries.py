from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional


def _get_by_path(doc: Dict[str, Any], path: str) -> Any:
    cur: Any = doc
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        if part not in cur:
            return None
        cur = cur[part]
    return cur


@dataclass(frozen=True)
class Query:
    """
    Query is a composable predicate: Query(doc) -> bool
    """
    _test: Callable[[Dict[str, Any]], bool]

    def __call__(self, doc: Dict[str, Any]) -> bool:
        try:
            return bool(self._test(doc))
        except Exception:
            return False

    def __and__(self, other: "Query") -> "Query":
        return Query(lambda d: self(d) and other(d))

    def __or__(self, other: "Query") -> "Query":
        return Query(lambda d: self(d) or other(d))

    def __invert__(self) -> "Query":
        return Query(lambda d: not self(d))


class Field:
    def __init__(self, path: str):
        self.path = path

    def exists(self) -> Query:
        return Query(lambda d: _get_by_path(d, self.path) is not None)

    def ==(self, other: Any) -> Query:  # type: ignore[misc]
        return Query(lambda d: _get_by_path(d, self.path) == other)

    def __eq__(self, other: Any) -> Query:  # noqa: Dunder; used for query DSL
        return Query(lambda d: _get_by_path(d, self.path) == other)

    def __ne__(self, other: Any) -> Query:
        return Query(lambda d: _get_by_path(d, self.path) != other)

    def __lt__(self, other: Any) -> Query:
        return Query(lambda d: (_get_by_path(d, self.path) is not None) and (_get_by_path(d, self.path) < other))

    def __le__(self, other: Any) -> Query:
        return Query(lambda d: (_get_by_path(d, self.path) is not None) and (_get_by_path(d, self.path) <= other))

    def __gt__(self, other: Any) -> Query:
        return Query(lambda d: (_get_by_path(d, self.path) is not None) and (_get_by_path(d, self.path) > other))

    def __ge__(self, other: Any) -> Query:
        return Query(lambda d: (_get_by_path(d, self.path) is not None) and (_get_by_path(d, self.path) >= other))

    def one_of(self, values: Iterable[Any]) -> Query:
        s = set(values)
        return Query(lambda d: _get_by_path(d, self.path) in s)

    def contains(self, item: Any) -> Query:
        def test(d: Dict[str, Any]) -> bool:
            v = _get_by_path(d, self.path)
            if v is None:
                return False
            if isinstance(v, (list, tuple, set)):
                return item in v
            if isinstance(v, str):
                return str(item) in v
            if isinstance(v, dict):
                return item in v
            return False
        return Query(test)

    def matches(self, func: Callable[[Any], bool]) -> Query:
        return Query(lambda d: func(_get_by_path(d, self.path)))

    def startswith(self, prefix: str) -> Query:
        return Query(lambda d: isinstance(_get_by_path(d, self.path), str) and _get_by_path(d, self.path).startswith(prefix))

    def endswith(self, suffix: str) -> Query:
        return Query(lambda d: isinstance(_get_by_path(d, self.path), str) and _get_by_path(d, self.path).endswith(suffix))


def where(path: str) -> Field:
    return Field(path)


def any_of(*queries: Query) -> Query:
    return Query(lambda d: any(q(d) for q in queries))


def all_of(*queries: Query) -> Query:
    return Query(lambda d: all(q(d) for q in queries))


def has_key(key: str) -> Query:
    return Query(lambda d: isinstance(d, dict) and key in d)


def doc_id_is(doc_id: int) -> Query:
    return Query(lambda d: int(d.get("id", -1)) == int(doc_id))


def project_is(project: str) -> Query:
    return where("project") == project


def status_is(status: str) -> Query:
    return where("status") == status


def unfinished() -> Query:
    return where("status") != "done"


def finished() -> Query:
    return where("status") == "done"


def due_before(ts: Any) -> Query:
    return where("due") < ts


def due_after(ts: Any) -> Query:
    return where("due") > ts


def text_contains(substr: str, field: str = "title") -> Query:
    return where(field).contains(substr)