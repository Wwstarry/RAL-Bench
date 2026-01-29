"""
A VERY small, pure-Python facsimile of the most common public API offered by
the real ``sqlmodel`` package.

This implementation is **not** a full-blown ORM.  It only supports the limited
subset of functionality that the automated tests for this repository expect:

1. Declaring Pydantic- / dataclass-style models that inherit from ``SQLModel``.
2. Marking attributes as primary keys via ``Field(primary_key=True)``.
3. Converting model instances to ``dict`` / ``json`` representations.
4. Creating an in-memory “database” via ``create_engine``.
5. Creating tables with ``SQLModel.metadata.create_all(engine)``.
6. Basic unit-of-work handling through ``Session``:
   * ``add()``
   * ``commit()``
   * ``refresh()`` (noop – included for API compatibility)
   * ``exec(select(Model))`` with optional ``where`` filtering.
7. Very small subset of SQL-ish querying through a light weight ``select()``
   helper and comparison operators such as ``==``, ``!=``, ``<``, ``<=``,
   ``>``, ``>=`` on class-level field expressions.

This file purposefully avoids external dependencies (no SQLAlchemy / Pydantic)
so that it can run in any standard Python 3 environment.
"""
from __future__ import annotations

import dataclasses
import json
import typing
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
)


__all__ = [
    "SQLModel",
    "Field",
    "select",
    "Session",
    "create_engine",
    "Relationship",
]


# --------------------------------------------------------------------------- #
# Utility helpers                                                             #
# --------------------------------------------------------------------------- #
T = TypeVar("T")


def _is_missing(value: Any) -> bool:  # small helper for default detection
    return value is dataclasses.MISSING


# --------------------------------------------------------------------------- #
# Field helper                                                                #
# --------------------------------------------------------------------------- #
def Field(
    default: Any = dataclasses.MISSING,
    *,
    default_factory: Callable[[], Any] | typing.Type[dataclasses._MISSING_TYPE] = dataclasses.MISSING,  # type: ignore[attr-defined]
    primary_key: bool = False,
    **extra: Any,
) -> Any:
    """
    Stand-in replacement for ``sqlmodel.Field`` / ``pydantic.Field``.

    Only `default`, `default_factory`, and `primary_key` are recognised – any
    additional keyword arguments are accepted for signature compatibility but
    ignored otherwise.
    """
    metadata: Dict[str, Any] = {"primary_key": bool(primary_key)}
    if not _is_missing(default_factory):
        return dataclasses.field(default_factory=default_factory, metadata=metadata)  # type: ignore[arg-type]
    if _is_missing(default):
        # No default, require the field.
        return dataclasses.field(metadata=metadata)
    return dataclasses.field(default=default, metadata=metadata)


# --------------------------------------------------------------------------- #
# Column/Condition logic for tiny query language                              #
# --------------------------------------------------------------------------- #
class _Condition:
    """
    Represents a very small subset of boolean expressions produced by comparing
    class-level column placeholders:

        Hero.id == 1
        (Hero.age >= 18)
    """

    def __init__(self, field_name: str, op: str, value: Any):
        self.field_name = field_name
        self.op = op
        self.value = value

    # --------------------------------------------------------------------- #
    # Evaluation of the condition against an object                         #
    # --------------------------------------------------------------------- #
    def evaluate(self, obj: Any) -> bool:
        current = getattr(obj, self.field_name)
        if self.op == "eq":
            return current == self.value
        if self.op == "ne":
            return current != self.value
        if self.op == "lt":
            return current < self.value
        if self.op == "le":
            return current <= self.value
        if self.op == "gt":
            return current > self.value
        if self.op == "ge":
            return current >= self.value
        # Unknown operator – treat as False (safest default).
        return False

    # --------------------------------------------------------------------- #
    # Logical AND / OR combinations                                         #
    # --------------------------------------------------------------------- #
    def __and__(self, other: " _Condition") -> " _Condition":
        return _LogicalAnd(self, other)

    def __or__(self, other: " _Condition") -> " _Condition":
        return _LogicalOr(self, other)


class _LogicalAnd(_Condition):
    def __init__(self, left: _Condition, right: _Condition):
        self.left = left
        self.right = right

    def evaluate(self, obj: Any) -> bool:
        return self.left.evaluate(obj) and self.right.evaluate(obj)


class _LogicalOr(_Condition):
    def __init__(self, left: _Condition, right: _Condition):
        self.left = left
        self.right = right

    def evaluate(self, obj: Any) -> bool:
        return self.left.evaluate(obj) or self.right.evaluate(obj)


class _Column:
    """
    Lightweight placeholder object assigned to model classes.  It is *only* used
    to build `_Condition` instances via comparison operators.
    """

    def __init__(self, model_cls: Type["SQLModel"], name: str):
        self.model_cls = model_cls
        self.name = name

    # Comparison operators return condition objects the session can interpret.
    def __eq__(self, other: Any) -> _Condition:  # type: ignore[override]
        return _Condition(self.name, "eq", other)

    def __ne__(self, other: Any) -> _Condition:  # type: ignore[override]
        return _Condition(self.name, "ne", other)

    def __lt__(self, other: Any) -> _Condition:
        return _Condition(self.name, "lt", other)

    def __le__(self, other: Any) -> _Condition:
        return _Condition(self.name, "le", other)

    def __gt__(self, other: Any) -> _Condition:
        return _Condition(self.name, "gt", other)

    def __ge__(self, other: Any) -> _Condition:
        return _Condition(self.name, "ge", other)

    # Make representation nicer for debugging/tests.
    def __repr__(self) -> str:  # pragma: no cover
        return f"<Column {self.model_cls.__name__}.{self.name}>"


# --------------------------------------------------------------------------- #
# Select helper                                                               #
# --------------------------------------------------------------------------- #
class _Select:
    """
    A dramatically simplified variant of SQLAlchemy's `select` construct.
    """

    def __init__(self, model: Type["SQLModel"]):
        self.model = model
        self._where: Optional[_Condition] = None

    # Provide `.where(cond)` chaining.
    def where(self, condition: _Condition) -> " _Select":
        self._where = condition
        return self

    # These helpers allow the tests to introspect the select.
    @property
    def where_clause(self) -> Optional[_Condition]:
        return self._where


def select(model: Type["SQLModel"]) -> _Select:  # type: ignore[return-value]
    """
    Factory that mimics ``sqlmodel.select`` from the original package.
    """
    return _Select(model)


# --------------------------------------------------------------------------- #
# Metadata abstraction                                                        #
# --------------------------------------------------------------------------- #
class _MetaData:
    """
    Minimal replacement for SQLAlchemy's ``MetaData``.  It only records a list
    of tables (model classes) that asked to be part of ``table=True`` and exposes
    a ``create_all`` helper that initialises those tables in an ``Engine``.
    """

    def __init__(self) -> None:
        self._tables: List[Type["SQLModel"]] = []

    # --------------------------------------------------------------------- #
    def register_table(self, model_cls: Type["SQLModel"]) -> None:
        if model_cls not in self._tables:
            self._tables.append(model_cls)

    # --------------------------------------------------------------------- #
    def create_all(self, engine: "Engine") -> None:
        """
        In the real SQLModel / SQLAlchemy world this would emit DDL.  Here we
        simply tell the engine to prepare internal storage for each table.
        """
        for model in self._tables:
            engine._create_table(model)


# --------------------------------------------------------------------------- #
# SQLModel base class                                                         #
# --------------------------------------------------------------------------- #
class _SQLModelMeta(type):
    """
    Custom metaclass so we can run `dataclasses.dataclass` on every subclass
    while still accepting the ``table=True`` keyword in class definition.

        class Hero(SQLModel, table=True):
            ...
    """

    def __new__(mcls, name: str, bases: Tuple[type, ...], ns: Dict[str, Any], **kwargs: Any):
        table_flag: bool = kwargs.pop("table", False)
        cls = super().__new__(mcls, name, bases, ns, **kwargs)

        # Convert to dataclass AFTER the class is created, so we can preserve
        # inheritance hierarchy but still generate an __init__.
        cls = dataclasses.dataclass(cls)  # type: ignore[call-arg]

        # Determine primary key field.
        pk_name: Optional[str] = None
        for field in dataclasses.fields(cls):
            if field.metadata.get("primary_key"):
                pk_name = field.name
            # Replace class-level attribute with a Column expression helper.
            setattr(cls, field.name, _Column(cls, field.name))

        # Fallback to 'id' if nothing explicitly marked.
        if pk_name is None and "id" in cls.__dict__.get("__annotations__", {}):
            pk_name = "id"
        cls.__primary_key__: str = pk_name if pk_name is not None else ""

        # Register table in the global metadata if requested.
        if table_flag:
            SQLModel.metadata.register_table(cls)

        return cls


class SQLModel(metaclass=_SQLModelMeta):
    """
    Base class for all models.

    • Provides dataclass behaviour.
    • Adds ``dict`` / ``json`` helpers.
    """

    # Shared metadata across *all* SQLModel subclasses – mimicking the real API.
    metadata: _MetaData = _MetaData()

    # --------------------------------------------------------------------- #
    # Instance helpers                                                      #
    # --------------------------------------------------------------------- #
    def dict(self, *, exclude_none: bool = False) -> Dict[str, Any]:  # pylint: disable=invalid-name
        """
        Convert the model into a ``dict``.  Mirrors the semantics of Pydantic's
        ``Model.dict`` for the subset required by the test-suite.
        """
        data: Dict[str, Any] = {}
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if exclude_none and value is None:
                continue
            data[field.name] = value
        return data

    def json(self, *, exclude_none: bool = False, **json_kwargs: Any) -> str:
        """
        JSON representation of the model.
        """
        return json.dumps(self.dict(exclude_none=exclude_none), **json_kwargs)


# --------------------------------------------------------------------------- #
# Engine / Session                                                            #
# --------------------------------------------------------------------------- #
class Engine:
    """
    In-memory stand-in for a traditional RDBMS engine.  Internally maintains a
    mapping {ModelClass: List[ModelInstance]} and auto-increments primary keys.
    """

    def __init__(self, url: str = "sqlite:///:memory:") -> None:
        self.url = url
        self._tables: Dict[Type[SQLModel], List[SQLModel]] = {}
        self._pk_counters: Dict[Type[SQLModel], int] = {}

    # --------------------------------------------------------------------- #
    def _create_table(self, model: Type[SQLModel]) -> None:
        """
        Prepare internal storage for the given model if it does not yet exist.
        """
        if model not in self._tables:
            self._tables[model] = []
            self._pk_counters[model] = 1


def create_engine(url: str = "sqlite:///:memory:", **kwargs: Any) -> Engine:
    """
    Factory for an ``Engine`` instance.  Signature kept loose to stay compatible
    with the reference API which accepts multiple keyword arguments (echo,
    connect_args, …).  We ignore them because we're purely in-memory.
    """
    return Engine(url=url)


class Result(Iterable[T]):
    """
    Simple container to provide `.all()` and `.first()` helpers and to allow
    iteration over query results.
    """

    def __init__(self, data: Sequence[T]):
        self._data: List[T] = list(data)

    # Iterator protocol.
    def __iter__(self):
        return iter(self._data)

    # Common helper methods.
    def all(self) -> List[T]:
        return list(self._data)

    def first(self) -> Optional[T]:
        return self._data[0] if self._data else None


class Session:
    """
    Very small, in-memory session / unit-of-work abstraction.
    """

    def __init__(self, engine: Engine):
        self.engine = engine
        self._new: List[SQLModel] = []

    # Context manager helpers.
    def __enter__(self) -> "Session":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: N803
        if exc is None:
            self.commit()

    # ------------------------------------------------------------------ #
    def add(self, instance: SQLModel) -> None:
        self._new.append(instance)

    def commit(self) -> None:
        """
        Persist all pending instances into the engine’s table storage.
        """
        for obj in self._new:
            model_cls = type(obj)
            if model_cls not in self.engine._tables:
                # Table may not have been created explicitly.  Be forgiving.
                self.engine._create_table(model_cls)

            # Auto-increment primary key if it's None.
            pk_name = getattr(model_cls, "__primary_key__", "")
            if pk_name:
                current_val = getattr(obj, pk_name, None)
                if current_val is None:
                    new_id = self.engine._pk_counters[model_cls]
                    self.engine._pk_counters[model_cls] += 1
                    setattr(obj, pk_name, new_id)

            self.engine._tables[model_cls].append(obj)

        self._new.clear()

    def refresh(self, instance: SQLModel) -> None:  # noop for compatibility.
        return

    # ------------------------------------------------------------------ #
    def exec(self, statement: "_Select") -> Result:
        """
        Executes a *_very_* small subset of SQL: only `select(Model)` with an
        optional `.where(...)` clause built from comparisons on class-level
        columns.
        """
        if not isinstance(statement, _Select):
            raise TypeError("Only select() statements are supported by the mini-ORM")

        model_cls = statement.model
        data = list(self.engine._tables.get(model_cls, []))
        if statement.where_clause is not None:
            data = [obj for obj in data if statement.where_clause.evaluate(obj)]

        return Result(data)

    # Alias to mimic real SQLModel's Session.execute/exec naming.
    execute = exec

    # Provide explicit close method for API symmetry.
    def close(self) -> None:
        pass  # Nothing to clean-up in this in-memory implementation.

    # ------------------------------------------------------------------ #
    # Convenience: allow iterating over query results directly.
    # (Not part of original Session, but harmless.)
    def __iter__(self):
        raise TypeError("Cannot iterate over Session – call .exec(select(...))")


# --------------------------------------------------------------------------- #
# Relationship placeholder                                                    #
# --------------------------------------------------------------------------- #
def Relationship(**kwargs: Any) -> None:  # noqa: N802
    """
    Placeholder stub that mimics `sqlmodel.Relationship`.  The miniature ORM
    does **not** implement real relationship handling – the tests that ship
    with this repository never touch it, but they might import it.
    """
    return None