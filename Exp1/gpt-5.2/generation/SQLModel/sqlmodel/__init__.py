"""
A lightweight, pure-Python subset of the SQLModel API.

This is NOT a full SQLModel/SQLAlchemy implementation. It provides the core
pieces commonly exercised in educational and black-box tests:
- Pydantic-like model declaration with annotations, defaults and validation
- Table modeling via SQLModel(table=True)
- Field(...) with primary_key, default, default_factory, nullable
- Basic SQLite engine utilities and a Session with add/commit/refresh/exec
- A minimal select() / where() query builder and simple expressions

Only SQLite is supported.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import json
import sqlite3
import threading
import types
import typing
from typing import Any, Callable, Dict, Generic, Iterable, List, Optional, Sequence, Tuple, Type, TypeVar, Union, get_args, get_origin

__all__ = [
    "SQLModel",
    "Field",
    "Relationship",
    "select",
    "Session",
    "create_engine",
]


# ----------------------------
# Field/Relationship utilities
# ----------------------------

_MISSING = object()


@dataclasses.dataclass
class FieldInfo:
    default: Any = _MISSING
    default_factory: Optional[Callable[[], Any]] = None
    primary_key: bool = False
    nullable: Optional[bool] = None
    index: bool = False
    unique: bool = False
    foreign_key: Optional[str] = None  # "table.col"
    sa_column: Any = None  # unused, compatibility stub
    description: Optional[str] = None
    title: Optional[str] = None


def Field(
    default: Any = _MISSING,
    *,
    default_factory: Optional[Callable[[], Any]] = None,
    primary_key: bool = False,
    nullable: Optional[bool] = None,
    index: bool = False,
    unique: bool = False,
    foreign_key: Optional[str] = None,
    sa_column: Any = None,
    description: Optional[str] = None,
    title: Optional[str] = None,
) -> Any:
    """Declare a model field (Pydantic/SQLModel-like)."""
    return FieldInfo(
        default=default,
        default_factory=default_factory,
        primary_key=primary_key,
        nullable=nullable,
        index=index,
        unique=unique,
        foreign_key=foreign_key,
        sa_column=sa_column,
        description=description,
        title=title,
    )


@dataclasses.dataclass
class RelationshipInfo:
    back_populates: Optional[str] = None
    link_model: Optional[Type[Any]] = None  # unused
    sa_relationship: Any = None  # unused
    cascade_delete: Optional[bool] = None  # unused


def Relationship(
    *,
    back_populates: Optional[str] = None,
    link_model: Optional[Type[Any]] = None,
    sa_relationship: Any = None,
    cascade_delete: Optional[bool] = None,
) -> Any:
    """Compatibility placeholder. No actual ORM relationship loading is implemented."""
    return RelationshipInfo(
        back_populates=back_populates,
        link_model=link_model,
        sa_relationship=sa_relationship,
        cascade_delete=cascade_delete,
    )


# ----------------------------
# Simple expression system
# ----------------------------

class Column:
    def __init__(self, model: Type["SQLModel"], name: str):
        self.model = model
        self.name = name

    def __repr__(self) -> str:
        return f"{self.model.__name__}.{self.name}"

    def _expr(self, op: str, value: Any) -> "BinaryExpression":
        return BinaryExpression(self, op, value)

    def __eq__(self, other: Any) -> "BinaryExpression":  # type: ignore[override]
        return self._expr("=", other)

    def __ne__(self, other: Any) -> "BinaryExpression":  # type: ignore[override]
        return self._expr("!=", other)

    def __lt__(self, other: Any) -> "BinaryExpression":
        return self._expr("<", other)

    def __le__(self, other: Any) -> "BinaryExpression":
        return self._expr("<=", other)

    def __gt__(self, other: Any) -> "BinaryExpression":
        return self._expr(">", other)

    def __ge__(self, other: Any) -> "BinaryExpression":
        return self._expr(">=", other)

    def in_(self, seq: Sequence[Any]) -> "InExpression":
        return InExpression(self, list(seq))

    def like(self, pattern: str) -> "BinaryExpression":
        return self._expr("LIKE", pattern)

    def is_(self, value: Any) -> "BinaryExpression":
        if value is None:
            return self._expr("IS", None)
        return self._expr("=", value)


class BinaryExpression:
    def __init__(self, col: Column, op: str, value: Any):
        self.col = col
        self.op = op
        self.value = value

    def to_sql(self) -> Tuple[str, List[Any]]:
        if self.op == "IS" and self.value is None:
            return f"{self.col.name} IS NULL", []
        return f"{self.col.name} {self.op} ?", [_adapt_value(self.value)]


class InExpression:
    def __init__(self, col: Column, values: List[Any]):
        self.col = col
        self.values = values

    def to_sql(self) -> Tuple[str, List[Any]]:
        if not self.values:
            return "1=0", []
        placeholders = ",".join(["?"] * len(self.values))
        return f"{self.col.name} IN ({placeholders})", [_adapt_value(v) for v in self.values]


# ----------------------------
# select() query builder
# ----------------------------

T = TypeVar("T")


class Select(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model
        self._where: List[Any] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._order_by: List[str] = []

    def where(self, *conditions: Any) -> "Select[T]":
        self._where.extend([c for c in conditions if c is not None])
        return self

    def limit(self, n: int) -> "Select[T]":
        self._limit = int(n)
        return self

    def offset(self, n: int) -> "Select[T]":
        self._offset = int(n)
        return self

    def order_by(self, *cols: Any) -> "Select[T]":
        # Accept Column or string
        for c in cols:
            if isinstance(c, Column):
                self._order_by.append(c.name)
            else:
                self._order_by.append(str(c))
        return self


def select(model: Type[T]) -> Select[T]:
    return Select(model)


# ----------------------------
# Engine & Session (SQLite)
# ----------------------------

class Engine:
    def __init__(self, url: str, *, echo: bool = False, connect_args: Optional[Dict[str, Any]] = None):
        self.url = url
        self.echo = echo
        self.connect_args = connect_args or {}
        self._local = threading.local()

    def _connect(self) -> sqlite3.Connection:
        if getattr(self._local, "conn", None) is None:
            if not self.url.startswith("sqlite:///"):
                raise ValueError("Only sqlite:/// URLs are supported")
            path = self.url[len("sqlite:///") :]
            if path == ":memory:":
                conn = sqlite3.connect(":memory:", check_same_thread=False, **self.connect_args)
            else:
                conn = sqlite3.connect(path, check_same_thread=False, **self.connect_args)
            conn.row_factory = sqlite3.Row
            setattr(self._local, "conn", conn)
        return typing.cast(sqlite3.Connection, self._local.conn)

    def execute(self, sql: str, params: Sequence[Any] = ()) -> sqlite3.Cursor:
        if self.echo:
            print(sql, params)
        cur = self._connect().cursor()
        cur.execute(sql, list(params))
        return cur

    def executemany(self, sql: str, seq_of_params: Sequence[Sequence[Any]]) -> sqlite3.Cursor:
        if self.echo:
            print(sql, seq_of_params)
        cur = self._connect().cursor()
        cur.executemany(sql, [list(p) for p in seq_of_params])
        return cur

    def commit(self) -> None:
        self._connect().commit()

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            setattr(self._local, "conn", None)


def create_engine(url: str, *, echo: bool = False, connect_args: Optional[Dict[str, Any]] = None) -> Engine:
    return Engine(url, echo=echo, connect_args=connect_args)


class Result(Generic[T]):
    def __init__(self, rows: List[Any]):
        self._rows = rows

    def all(self) -> List[Any]:
        return list(self._rows)

    def first(self) -> Any:
        return self._rows[0] if self._rows else None

    def one(self) -> Any:
        if len(self._rows) != 1:
            raise ValueError("Expected exactly one row")
        return self._rows[0]

    def one_or_none(self) -> Any:
        if len(self._rows) == 0:
            return None
        if len(self._rows) != 1:
            raise ValueError("Expected zero or one row")
        return self._rows[0]


class Session:
    def __init__(self, engine: Engine):
        self.engine = engine
        self._new: List[SQLModel] = []
        self._closed = False

    def __enter__(self) -> "Session":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        # no automatic commit
        self.close()

    def close(self) -> None:
        self._closed = True

    def add(self, instance: "SQLModel") -> None:
        self._new.append(instance)

    def add_all(self, instances: Iterable["SQLModel"]) -> None:
        for i in instances:
            self.add(i)

    def commit(self) -> None:
        # Insert pending
        for inst in list(self._new):
            self._insert(inst)
        self._new.clear()
        self.engine.commit()

    def refresh(self, instance: "SQLModel") -> None:
        model = type(instance)
        pk_name = _primary_key_name(model)
        pk_val = getattr(instance, pk_name, None)
        if pk_val is None:
            return
        stmt = select(model).where(getattr(model, pk_name) == pk_val)
        obj = self.exec(stmt).first()
        if obj is None:
            return
        for f in model.__fields__.keys():
            setattr(instance, f, getattr(obj, f, None))

    def exec(self, statement: Any) -> Result[Any]:
        if isinstance(statement, Select):
            return self._exec_select(statement)
        # raw SQL
        if isinstance(statement, str):
            cur = self.engine.execute(statement)
            try:
                rows = cur.fetchall()
            except sqlite3.ProgrammingError:
                rows = []
            return Result(rows)
        raise TypeError("Unsupported statement type")

    # Compatibility alias used by some tests
    execute = exec

    def _insert(self, instance: "SQLModel") -> None:
        model = type(instance)
        if not getattr(model, "__table__", False):
            raise ValueError("Instance model is not a table model (table=True)")
        table = model.__tablename__
        fields = model.__fields__
        pk = _primary_key_name(model)

        cols: List[str] = []
        vals: List[Any] = []
        for name, finfo in fields.items():
            if name == pk and getattr(instance, name, None) is None and finfo.primary_key:
                continue  # autoincrement
            cols.append(name)
            vals.append(_adapt_value(getattr(instance, name, None)))

        if cols:
            placeholders = ",".join(["?"] * len(cols))
            sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
            cur = self.engine.execute(sql, vals)
        else:
            sql = f"INSERT INTO {table} DEFAULT VALUES"
            cur = self.engine.execute(sql, [])

        # set autoincrement pk
        if getattr(instance, pk, None) is None:
            try:
                setattr(instance, pk, cur.lastrowid)
            except Exception:
                pass

    def _exec_select(self, stmt: Select[Any]) -> Result[Any]:
        model = stmt.model
        if not getattr(model, "__table__", False):
            raise ValueError("select() only supports table models")
        table = model.__tablename__
        cols = list(model.__fields__.keys())
        sql = f"SELECT {', '.join(cols)} FROM {table}"
        params: List[Any] = []

        if stmt._where:
            where_parts: List[str] = []
            for c in stmt._where:
                if hasattr(c, "to_sql"):
                    wsql, wparams = c.to_sql()
                    where_parts.append(wsql)
                    params.extend(wparams)
                else:
                    raise TypeError("Unsupported where condition")
            sql += " WHERE " + " AND ".join(where_parts)

        if stmt._order_by:
            sql += " ORDER BY " + ", ".join(stmt._order_by)
        if stmt._limit is not None:
            sql += " LIMIT ?"
            params.append(int(stmt._limit))
        if stmt._offset is not None:
            sql += " OFFSET ?"
            params.append(int(stmt._offset))

        cur = self.engine.execute(sql, params)
        rows = cur.fetchall()
        objs: List[Any] = []
        for r in rows:
            data = dict(r)
            objs.append(model(**data))
        return Result(objs)


# ----------------------------
# SQLModel base class & metaclass
# ----------------------------

def _is_optional(tp: Any) -> bool:
    origin = get_origin(tp)
    if origin is Union:
        args = get_args(tp)
        return any(a is type(None) for a in args)
    return False


def _strip_optional(tp: Any) -> Any:
    origin = get_origin(tp)
    if origin is Union:
        args = [a for a in get_args(tp) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return tp


def _python_to_sql_type(tp: Any) -> str:
    tp = _strip_optional(tp)
    origin = get_origin(tp)
    if origin in (list, List, dict, Dict, tuple, Tuple, set, typing.Set):
        return "TEXT"
    if tp in (int,):
        return "INTEGER"
    if tp in (float,):
        return "REAL"
    if tp in (bool,):
        return "INTEGER"
    if tp in (str,):
        return "TEXT"
    if tp in (_dt.date, _dt.datetime):
        return "TEXT"
    return "TEXT"


def _adapt_value(v: Any) -> Any:
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, (_dt.datetime, _dt.date)):
        return v.isoformat()
    if isinstance(v, (dict, list, tuple, set)):
        return json.dumps(v, separators=(",", ":"), sort_keys=True, default=str)
    return v


def _cast_value(tp: Any, v: Any) -> Any:
    if v is None:
        return None
    tp0 = _strip_optional(tp)
    try:
        if tp0 is bool:
            if isinstance(v, str):
                if v.lower() in ("true", "1", "yes", "y", "t"):
                    return True
                if v.lower() in ("false", "0", "no", "n", "f"):
                    return False
            return bool(int(v)) if isinstance(v, (int, float, str)) else bool(v)
        if tp0 is int:
            return int(v)
        if tp0 is float:
            return float(v)
        if tp0 is str:
            return str(v)
        if tp0 is _dt.datetime:
            if isinstance(v, _dt.datetime):
                return v
            return _dt.datetime.fromisoformat(str(v))
        if tp0 is _dt.date:
            if isinstance(v, _dt.date) and not isinstance(v, _dt.datetime):
                return v
            return _dt.date.fromisoformat(str(v))
    except Exception:
        return v
    return v


def _primary_key_name(model: Type["SQLModel"]) -> str:
    for n, f in model.__fields__.items():
        if f.primary_key:
            return n
    # fallback
    return "id"


class SQLModelMeta(type):
    def __new__(mcls, name, bases, namespace, **kwargs):
        table = bool(kwargs.pop("table", namespace.pop("__table__", False)))
        cls = super().__new__(mcls, name, bases, dict(namespace))

        # inherit fields
        fields: Dict[str, FieldInfo] = {}
        annotations: Dict[str, Any] = {}
        for b in reversed(cls.__mro__[1:]):
            if hasattr(b, "__fields__"):
                fields.update(getattr(b, "__fields__"))
            if hasattr(b, "__annotations__"):
                annotations.update(getattr(b, "__annotations__"))

        annotations.update(namespace.get("__annotations__", {}))

        # Build fields based on annotations + defaults/FieldInfo
        for fname, ftype in annotations.items():
            if fname.startswith("_"):
                continue
            default = getattr(cls, fname, _MISSING)
            if isinstance(default, (FieldInfo, RelationshipInfo)):
                finfo = default if isinstance(default, FieldInfo) else FieldInfo(default=_MISSING)
                # Replace class attribute with Column for table models later
                if isinstance(default, RelationshipInfo):
                    # keep relationship info
                    continue
            else:
                finfo = FieldInfo(default=default)
            # if no explicit nullable, infer from Optional
            if finfo.nullable is None:
                finfo.nullable = _is_optional(ftype) or finfo.default is None or finfo.default_factory is not None
            fields[fname] = finfo

        cls.__fields__ = fields
        cls.__annotations__ = annotations

        # Table configuration
        cls.__table__ = table
        if table:
            tablename = getattr(cls, "__tablename__", None) or name.lower()
            cls.__tablename__ = tablename

            # Create Column descriptors for expressions
            for fname in list(fields.keys()):
                setattr(cls, fname, Column(cls, fname))

        return cls


class SQLModel(metaclass=SQLModelMeta):
    __fields__: Dict[str, FieldInfo]
    __table__: bool = False
    __tablename__: str

    def __init__(self, **data: Any):
        # Prepare values using defaults and type casting
        for fname, finfo in self.__fields__.items():
            ftype = self.__annotations__.get(fname, Any)

            if fname in data:
                value = data[fname]
            else:
                if finfo.default_factory is not None:
                    value = finfo.default_factory()
                elif finfo.default is not _MISSING:
                    value = finfo.default
                else:
                    value = None

            # validate nullability (lightweight)
            if value is None and finfo.nullable is False:
                raise ValueError(f"Field '{fname}' cannot be None")

            value = _cast_value(ftype, value)
            object.__setattr__(self, fname, value)

    # Allow attribute setting
    def __setattr__(self, key: str, value: Any) -> None:
        if key in getattr(self, "__fields__", {}):
            tp = self.__annotations__.get(key, Any)
            finfo = self.__fields__[key]
            if value is None and finfo.nullable is False:
                raise ValueError(f"Field '{key}' cannot be None")
            object.__setattr__(self, key, _cast_value(tp, value))
            return
        object.__setattr__(self, key, value)

    def dict(self, *, exclude_none: bool = False) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for fname in self.__fields__.keys():
            v = getattr(self, fname, None)
            if exclude_none and v is None:
                continue
            out[fname] = v
        return out

    def json(self, *, exclude_none: bool = False) -> str:
        return json.dumps(self.dict(exclude_none=exclude_none), default=str, separators=(",", ":"), sort_keys=True)

    def model_dump(self, *, exclude_none: bool = False) -> Dict[str, Any]:
        # Pydantic v2-ish alias used by some tests
        return self.dict(exclude_none=exclude_none)

    def model_dump_json(self, *, exclude_none: bool = False) -> str:
        return self.json(exclude_none=exclude_none)

    @classmethod
    def model_validate(cls: Type[T], obj: Any) -> T:
        if isinstance(obj, cls):
            return obj
        if isinstance(obj, dict):
            return cls(**obj)
        raise TypeError("model_validate expects a dict or instance")

    def __repr__(self) -> str:
        vals = ", ".join(f"{k}={getattr(self, k, None)!r}" for k in self.__fields__.keys())
        return f"{type(self).__name__}({vals})"


# ----------------------------
# Metadata + create_all
# ----------------------------

class _SQLModelMetadata:
    def __init__(self):
        self._tables: Dict[str, Type[SQLModel]] = {}

    def register(self, model: Type[SQLModel]) -> None:
        if getattr(model, "__table__", False):
            self._tables[model.__tablename__] = model

    def create_all(self, engine: Engine) -> None:
        for _, model in list(self._tables.items()):
            _create_table_for_model(engine, model)


def _create_table_for_model(engine: Engine, model: Type[SQLModel]) -> None:
    cols_sql: List[str] = []
    for fname, finfo in model.__fields__.items():
        ftype = model.__annotations__.get(fname, Any)
        coltype = _python_to_sql_type(ftype)

        parts = [fname, coltype]

        if finfo.primary_key:
            # Prefer INTEGER PRIMARY KEY AUTOINCREMENT when int-ish
            if _strip_optional(ftype) is int and coltype == "INTEGER":
                parts = [fname, "INTEGER", "PRIMARY KEY", "AUTOINCREMENT"]
            else:
                parts.append("PRIMARY KEY")

        # Nullability
        if finfo.nullable is False:
            parts.append("NOT NULL")

        if finfo.unique:
            parts.append("UNIQUE")

        # Foreign key (simple)
        if finfo.foreign_key:
            try:
                ref_table, ref_col = finfo.foreign_key.split(".", 1)
                parts.append(f"REFERENCES {ref_table}({ref_col})")
            except Exception:
                pass

        cols_sql.append(" ".join(parts))

    sql = f"CREATE TABLE IF NOT EXISTS {model.__tablename__} ({', '.join(cols_sql)})"
    engine.execute(sql)
    engine.commit()


# attach SQLModel.metadata compatible attribute
SQLModel.metadata = _SQLModelMetadata()

# Register table models automatically by hooking metaclass creation: we cannot
# easily intercept after class creation here, so provide helper via __init_subclass__.
def _sqlmodel_init_subclass(cls, **kwargs):
    # register if table
    if getattr(cls, "__table__", False):
        SQLModel.metadata.register(cls)

SQLModel.__init_subclass__ = classmethod(_sqlmodel_init_subclass)  # type: ignore