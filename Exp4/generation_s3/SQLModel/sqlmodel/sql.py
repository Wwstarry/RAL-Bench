from __future__ import annotations

import typing as t

from .orm import Column, Condition


class Select:
    def __init__(self, *entities: t.Any):
        if not entities:
            raise TypeError("select() requires at least one entity")
        self.entities = entities
        self._where: list[Condition] = []
        self._limit: t.Optional[int] = None
        self._offset: int = 0
        self._order_by: list[t.Any] = []

    def where(self, condition: Condition) -> "Select":
        self._where.append(condition)
        return self

    def limit(self, n: int) -> "Select":
        self._limit = int(n)
        return self

    def offset(self, n: int) -> "Select":
        self._offset = int(n)
        return self

    def order_by(self, *cols: t.Any) -> "Select":
        self._order_by.extend(cols)
        return self


def select(*entities: t.Any) -> Select:
    return Select(*entities)


class Row(tuple):
    __slots__ = ()

    def __new__(cls, items: tuple):
        return super().__new__(cls, items)

    def __repr__(self) -> str:
        return f"Row{tuple.__repr__(self)}"


class ScalarResult:
    def __init__(self, values: list[t.Any]):
        self._values = values

    def all(self) -> list[t.Any]:
        return list(self._values)

    def first(self) -> t.Any:
        return self._values[0] if self._values else None

    def one(self) -> t.Any:
        if len(self._values) != 1:
            raise ValueError("Expected exactly one row")
        return self._values[0]

    def one_or_none(self) -> t.Any:
        if len(self._values) == 0:
            return None
        if len(self._values) != 1:
            raise ValueError("Expected at most one row")
        return self._values[0]


class Result:
    def __init__(self, rows: list[t.Any], *, scalar_index: t.Optional[int] = None):
        self._rows = rows
        self._scalar_index = scalar_index

    def all(self) -> list[t.Any]:
        return list(self._rows)

    def first(self) -> t.Any:
        return self._rows[0] if self._rows else None

    def one(self) -> t.Any:
        if len(self._rows) != 1:
            raise ValueError("Expected exactly one row")
        return self._rows[0]

    def one_or_none(self) -> t.Any:
        if len(self._rows) == 0:
            return None
        if len(self._rows) != 1:
            raise ValueError("Expected at most one row")
        return self._rows[0]

    def scalars(self) -> ScalarResult:
        if self._scalar_index is None:
            if self._rows and isinstance(self._rows[0], Row):
                values = [r[0] for r in self._rows]
            else:
                values = list(self._rows)
        else:
            values = []
            for r in self._rows:
                if isinstance(r, Row):
                    values.append(r[self._scalar_index])
                else:
                    values.append(r)
        return ScalarResult(values)