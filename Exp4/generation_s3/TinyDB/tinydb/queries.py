from __future__ import annotations

import re
from typing import Any, Callable, Iterable


_MISSING = object()


class Query:
    """
    Query objects are both:
      - path builders (where("a").b.c), and
      - predicates (callable) once an operation is applied.
    """

    def __init__(self, path: tuple[str, ...] = (), _predicate: Callable[[dict], bool] | None = None) -> None:
        self._path = tuple(path)
        self._predicate = _predicate

    # ----- Path building -----

    def __getattr__(self, item: str) -> "Query":
        if item.startswith("_"):
            raise AttributeError(item)
        return Query(self._path + (item,), None)

    def __getitem__(self, item: str) -> "Query":
        if not isinstance(item, str):
            raise TypeError("Query keys must be strings")
        if item.startswith("_"):
            raise AttributeError(item)
        return Query(self._path + (item,), None)

    # ----- Helpers -----

    def _resolve(self, document: dict) -> Any:
        cur: Any = document
        for key in self._path:
            if not isinstance(cur, dict) or key not in cur:
                return _MISSING
            cur = cur[key]
        return cur

    def _exists(self, document: dict) -> bool:
        cur: Any = document
        for key in self._path:
            if not isinstance(cur, dict) or key not in cur:
                return False
            cur = cur[key]
        return True

    def _with_predicate(self, pred: Callable[[dict], bool]) -> "Query":
        return Query(self._path, pred)

    # ----- Evaluation -----

    def __call__(self, document: dict) -> bool:
        if self._predicate is None:
            # A plain path builder is not a valid predicate.
            raise TypeError("Incomplete query: no operation specified")
        return bool(self._predicate(document))

    # ----- Comparisons -----

    def __eq__(self, other: Any) -> "Query":  # type: ignore[override]
        def pred(doc: dict) -> bool:
            v = self._resolve(doc)
            if v is _MISSING:
                return False
            return v == other

        return self._with_predicate(pred)

    def __ne__(self, other: Any) -> "Query":  # type: ignore[override]
        def pred(doc: dict) -> bool:
            v = self._resolve(doc)
            if v is _MISSING:
                return False
            return v != other

        return self._with_predicate(pred)

    def __lt__(self, other: Any) -> "Query":
        def pred(doc: dict) -> bool:
            v = self._resolve(doc)
            if v is _MISSING:
                return False
            try:
                return v < other
            except Exception:
                return False

        return self._with_predicate(pred)

    def __le__(self, other: Any) -> "Query":
        def pred(doc: dict) -> bool:
            v = self._resolve(doc)
            if v is _MISSING:
                return False
            try:
                return v <= other
            except Exception:
                return False

        return self._with_predicate(pred)

    def __gt__(self, other: Any) -> "Query":
        def pred(doc: dict) -> bool:
            v = self._resolve(doc)
            if v is _MISSING:
                return False
            try:
                return v > other
            except Exception:
                return False

        return self._with_predicate(pred)

    def __ge__(self, other: Any) -> "Query":
        def pred(doc: dict) -> bool:
            v = self._resolve(doc)
            if v is _MISSING:
                return False
            try:
                return v >= other
            except Exception:
                return False

        return self._with_predicate(pred)

    # ----- Additional operators -----

    def exists(self) -> "Query":
        def pred(doc: dict) -> bool:
            return self._exists(doc)

        return self._with_predicate(pred)

    def one_of(self, values: Iterable[Any]) -> "Query":
        # values can be list/set/tuple; we'll use "in"
        def pred(doc: dict) -> bool:
            v = self._resolve(doc)
            if v is _MISSING:
                return False
            return v in values

        return self._with_predicate(pred)

    def matches(self, pattern: str) -> "Query":
        rx = re.compile(pattern)

        def pred(doc: dict) -> bool:
            v = self._resolve(doc)
            if v is _MISSING or not isinstance(v, str):
                return False
            return rx.search(v) is not None

        return self._with_predicate(pred)

    def test(self, func: Callable[[Any], bool]) -> "Query":
        def pred(doc: dict) -> bool:
            v = self._resolve(doc)
            if v is _MISSING:
                # Contract allows passing None, but simplest is to call with None.
                v2 = None
            else:
                v2 = v
            try:
                return bool(func(v2))
            except Exception:
                return False

        return self._with_predicate(pred)

    # ----- Boolean composition -----

    def __and__(self, other: "Query") -> "Query":
        if not isinstance(other, Query):
            return NotImplemented  # type: ignore[return-value]

        def pred(doc: dict) -> bool:
            return bool(self(doc)) and bool(other(doc))

        return Query((), pred)

    def __or__(self, other: "Query") -> "Query":
        if not isinstance(other, Query):
            return NotImplemented  # type: ignore[return-value]

        def pred(doc: dict) -> bool:
            return bool(self(doc)) or bool(other(doc))

        return Query((), pred)

    def __invert__(self) -> "Query":
        def pred(doc: dict) -> bool:
            return not bool(self(doc))

        return Query((), pred)


def where(key: str) -> Query:
    if not isinstance(key, str):
        raise TypeError("where(key) expects a string key")
    if key.startswith("_"):
        raise AttributeError(key)
    return Query((key,), None)