"""
Very small query DSL inspired by TinyDB.

Usage
------
>>> from tinydb.queries import Query
>>> User = Query()
>>> (User.name == 'Alice') & (User.done == False)
<Condition ...>
"""

from __future__ import annotations

import operator
from typing import Any, Callable


class Condition:
    """
    Wraps a boolean function(doc) -> bool and provides &, | and ~ operators for
    boolean algebra.
    """

    __slots__ = ("_test",)

    def __init__(self, test: Callable[[dict], bool]):
        self._test = test

    # ------------------------------------------------------------------ #
    # Composition
    # ------------------------------------------------------------------ #
    def __call__(self, document: dict) -> bool:
        try:
            return bool(self._test(document))
        except Exception:
            # Safety: any exception in user test counts as "no match"
            return False

    def __and__(self, other: "Condition") -> "Condition":
        return Condition(lambda doc: self(doc) and other(doc))

    def __or__(self, other: "Condition") -> "Condition":
        return Condition(lambda doc: self(doc) or other(doc))

    def __invert__(self) -> "Condition":
        return Condition(lambda doc: not self(doc))

    # ------------------------------------------------------------------ #
    # Misc
    # ------------------------------------------------------------------ #
    def __repr__(self) -> str:
        return f"<Condition {id(self):x}>"


# -------------------------------------------------------------------------- #
# QueryField
# -------------------------------------------------------------------------- #
class QueryField:
    """
    Represents a single "path" in the targeted document, e.g.
        Query().foo.bar   ->  path ('foo', 'bar')
    """

    __slots__ = ("_path",)

    def __init__(self, path: tuple[str, ...]):
        self._path = path

    # ------------------------------------------------------------------ #
    # Attribute traversal
    # ------------------------------------------------------------------ #
    def __getattr__(self, item: str) -> "QueryField":
        return QueryField(self._path + (item,))

    # ------------------------------------------------------------------ #
    # Comparison operators
    # ------------------------------------------------------------------ #
    def _cmp(self, op: Callable[[Any, Any], bool], other) -> Condition:
        def _test(document):
            current = document
            for key in self._path:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return False
            try:
                return op(current, other)
            except Exception:
                return False

        return Condition(_test)

    def __eq__(self, other):  # type: ignore
        return self._cmp(operator.eq, other)

    def __ne__(self, other):  # type: ignore
        return self._cmp(operator.ne, other)

    def __lt__(self, other):
        return self._cmp(operator.lt, other)

    def __le__(self, other):
        return self._cmp(operator.le, other)

    def __gt__(self, other):
        return self._cmp(operator.gt, other)

    def __ge__(self, other):
        return self._cmp(operator.ge, other)

    # Matching / existence helpers
    def exists(self) -> Condition:
        return Condition(
            lambda doc: self._drill(doc, default=_Missing) is not _Missing
        )

    def matches(self, predicate: Callable[[Any], bool]) -> Condition:
        return Condition(
            lambda doc: predicate(self._drill(doc, default=_Missing))
            if self._drill(doc, default=_Missing) is not _Missing
            else False
        )

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    def _drill(self, document: dict, default=_Ellipsis := object()):
        current = document
        for key in self._path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current


# -------------------------------------------------------------------------- #
# Query root
# -------------------------------------------------------------------------- #
class Query:
    """
    Entry point for building queries.

    Query().foo == 3
    """

    __slots__ = ()

    def __getattr__(self, item: str) -> QueryField:
        return QueryField((item,))