from __future__ import annotations

import typing as t

from .exceptions import MultiplePrimaryKeyError


class RelationshipInfo:
    __slots__ = ("back_populates", "link_model", "sa_relationship_kwargs", "extra")

    def __init__(
        self,
        *,
        back_populates: t.Optional[str] = None,
        link_model: t.Any = None,
        sa_relationship_kwargs: t.Optional[dict] = None,
        **extra: t.Any,
    ):
        self.back_populates = back_populates
        self.link_model = link_model
        self.sa_relationship_kwargs = sa_relationship_kwargs or None
        self.extra = dict(extra)


def Relationship(
    *,
    back_populates: t.Optional[str] = None,
    link_model: t.Any = None,
    sa_relationship_kwargs: t.Optional[dict] = None,
    **extra: t.Any,
) -> t.Any:
    return RelationshipInfo(
        back_populates=back_populates,
        link_model=link_model,
        sa_relationship_kwargs=sa_relationship_kwargs,
        **extra,
    )


class Column:
    def __init__(
        self,
        model_cls: type,
        name: str,
        python_type: t.Any,
        *,
        primary_key: bool = False,
        nullable: bool = True,
        default: t.Any = None,
        index: bool = False,
        unique: bool = False,
    ):
        self.model_cls = model_cls
        self.name = name
        self.python_type = python_type
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.index = index
        self.unique = unique

    def __repr__(self) -> str:
        return f"{self.model_cls.__name__}.{self.name}"

    def _cmp(self, op: str, other: t.Any) -> "Condition":
        return Condition(self, op, other)

    def __eq__(self, other: t.Any) -> "Condition":  # type: ignore[override]
        return self._cmp("==", other)

    def __ne__(self, other: t.Any) -> "Condition":  # type: ignore[override]
        return self._cmp("!=", other)

    def __lt__(self, other: t.Any) -> "Condition":
        return self._cmp("<", other)

    def __le__(self, other: t.Any) -> "Condition":
        return self._cmp("<=", other)

    def __gt__(self, other: t.Any) -> "Condition":
        return self._cmp(">", other)

    def __ge__(self, other: t.Any) -> "Condition":
        return self._cmp(">=", other)

    def in_(self, values: t.Iterable[t.Any]) -> "Condition":
        return self._cmp("in", list(values))


class Condition:
    def __init__(self, left: t.Any, op: str, right: t.Any):
        self.left = left
        self.op = op
        self.right = right

    def __and__(self, other: "Condition") -> "BoolCondition":
        return BoolCondition("and", [self, other])

    def __or__(self, other: "Condition") -> "BoolCondition":
        return BoolCondition("or", [self, other])

    def __repr__(self) -> str:
        return f"({self.left!r} {self.op} {self.right!r})"

    def eval(self, row: dict) -> bool:
        if isinstance(self.left, Column):
            lval = row.get(self.left.name)
        else:
            lval = self.left

        rval = self.right
        if isinstance(rval, Column):
            rval = row.get(rval.name)

        if self.op == "==":
            return lval == rval
        if self.op == "!=":
            return lval != rval
        if self.op == "<":
            return lval < rval
        if self.op == "<=":
            return lval <= rval
        if self.op == ">":
            return lval > rval
        if self.op == ">=":
            return lval >= rval
        if self.op == "in":
            return lval in (rval or [])
        raise ValueError(f"Unknown operator: {self.op}")


class BoolCondition(Condition):
    def __init__(self, mode: str, conditions: list[Condition]):
        self.mode = mode
        self.conditions = conditions
        super().__init__(left=None, op=mode, right=None)

    def __and__(self, other: Condition) -> "BoolCondition":
        if self.mode == "and":
            return BoolCondition("and", self.conditions + [other])
        return BoolCondition("and", [self, other])

    def __or__(self, other: Condition) -> "BoolCondition":
        if self.mode == "or":
            return BoolCondition("or", self.conditions + [other])
        return BoolCondition("or", [self, other])

    def __repr__(self) -> str:
        join = " AND " if self.mode == "and" else " OR "
        return "(" + join.join(repr(c) for c in self.conditions) + ")"

    def eval(self, row: dict) -> bool:
        if self.mode == "and":
            return all(c.eval(row) for c in self.conditions)
        return any(c.eval(row) for c in self.conditions)


class Table:
    def __init__(self, name: str, model_cls: type, columns: dict[str, Column]):
        self.name = name
        self.model_cls = model_cls
        self.columns = columns

        pks = [c for c in columns.values() if c.primary_key]
        if len(pks) > 1:
            raise MultiplePrimaryKeyError("Only a single primary key column is supported")
        self.primary_key: t.Optional[Column] = pks[0] if pks else None

    def __repr__(self) -> str:
        return f"Table({self.name})"


class MetaData:
    def __init__(self):
        self.tables: dict[str, Table] = {}

    def create_all(self, engine: "Engine") -> None:
        from .engine import Engine  # local import to avoid cycle

        if not isinstance(engine, Engine):
            raise TypeError("engine must be an Engine")
        for table in self.tables.values():
            engine._ensure_table(table)

    def drop_all(self, engine: "Engine") -> None:
        from .engine import Engine  # local import to avoid cycle

        if not isinstance(engine, Engine):
            raise TypeError("engine must be an Engine")
        engine._drop_all()