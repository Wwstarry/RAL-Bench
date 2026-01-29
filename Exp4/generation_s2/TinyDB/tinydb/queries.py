from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional, Sequence


Predicate = Callable[[dict], bool]


@dataclass(frozen=True)
class Query:
    """
    A composable predicate for filtering documents.

    Query objects are callable: Query(doc) -> bool.
    Use `where("field")` to start building expressions.

    Examples:
        from tinydb import where
        Task = where("type") == "task"
        Open = where("status") != "done"
        q = Task & Open & where("project").one_of(["p1", "p2"])
    """
    _test: Predicate

    def __call__(self, doc: dict) -> bool:
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
    def __init__(self, path: str) -> None:
        if not isinstance(path, str) or not path:
            raise ValueError("path must be a non-empty string")
        self._path = path

    @property
    def path(self) -> str:
        return self._path

    def _get(self, doc: dict) -> Any:
        cur: Any = doc
        for part in self._path.split("."):
            if not isinstance(cur, dict):
                return None
            cur = cur.get(part, None)
        return cur

    # Comparisons
    def __eq__(self, other: Any) -> Query:  # type: ignore[override]
        return Query(lambda d: self._get(d) == other)

    def __ne__(self, other: Any) -> Query:  # type: ignore[override]
        return Query(lambda d: self._get(d) != other)

    def __lt__(self, other: Any) -> Query:
        return Query(lambda d: (v := self._get(d)) is not None and v < other)

    def __le__(self, other: Any) -> Query:
        return Query(lambda d: (v := self._get(d)) is not None and v <= other)

    def __gt__(self, other: Any) -> Query:
        return Query(lambda d: (v := self._get(d)) is not None and v > other)

    def __ge__(self, other: Any) -> Query:
        return Query(lambda d: (v := self._get(d)) is not None and v >= other)

    # String helpers
    def exists(self) -> Query:
        return Query(lambda d: self._get(d) is not None)

    def matches(self, predicate: Callable[[Any], bool]) -> Query:
        return Query(lambda d: predicate(self._get(d)))

    def contains(self, item: Any) -> Query:
        def _p(d: dict) -> bool:
            v = self._get(d)
            if isinstance(v, (list, tuple, set)):
                return item in v
            if isinstance(v, str):
                return str(item) in v
            if isinstance(v, dict):
                return item in v
            return False

        return Query(_p)

    def one_of(self, items: Iterable[Any]) -> Query:
        s = set(items)
        return Query(lambda d: self._get(d) in s)

    def test(self, func: Callable[[Any], bool]) -> Query:
        return Query(lambda d: func(self._get(d)))


def where(field_path: str) -> Field:
    return Field(field_path)