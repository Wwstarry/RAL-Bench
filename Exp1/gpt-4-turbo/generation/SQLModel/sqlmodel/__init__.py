import sqlite3
import json
import threading
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, get_type_hints

T = TypeVar("T", bound="SQLModel")

# --- Field definition ---
class FieldInfo:
    def __init__(
        self,
        default: Any = ...,
        primary_key: bool = False,
        foreign_key: Optional[str] = None,
        nullable: Optional[bool] = None,
        index: bool = False,
        **kwargs,
    ):
        self.default = default
        self.primary_key = primary_key
        self.foreign_key = foreign_key
        self.nullable = nullable
        self.index = index
        self.extra = kwargs

def Field(
    default: Any = ...,
    *,
    primary_key: bool = False,
    foreign_key: Optional[str] = None,
    nullable: Optional[bool] = None,
    index: bool = False,
    **kwargs,
) -> Any:
    return FieldInfo(
        default=default,
        primary_key=primary_key,
        foreign_key=foreign_key,
        nullable=nullable,
        index=index,
        **kwargs,
    )

# --- Relationship stub (not implemented, for API compatibility) ---
def Relationship(*args, **kwargs):
    # For API compatibility; not implemented in pure Python version
    return None

# --- SQLModel metaclass and base ---
class SQLModelMeta(type):
    def __new__(mcs, name, bases, namespace):
        annotations = namespace.get("__annotations__", {})
        fields = {}
        primary_keys = []
        for base in bases:
            if hasattr(base, "__fields__"):
                fields.update(base.__fields__)
            if hasattr(base, "__primary_keys__"):
                primary_keys.extend(base.__primary_keys__)
        for field_name, field_type in annotations.items():
            field_value = namespace.get(field_name, ...)
            if isinstance(field_value, FieldInfo):
                info = field_value
            else:
                info = FieldInfo(default=field_value)
            fields[field_name] = (field_type, info)
            if info.primary_key:
                primary_keys.append(field_name)
        namespace["__fields__"] = fields
        namespace["__primary_keys__"] = primary_keys
        namespace["__tablename__"] = namespace.get("__tablename__", name.lower())
        return super().__new__(mcs, name, bases, namespace)

class SQLModel(metaclass=SQLModelMeta):
    def __init__(self, **kwargs):
        for field, (typ, info) in self.__fields__.items():
            if field in kwargs:
                value = kwargs[field]
            elif info.default is not ...:
                value = info.default
            else:
                value = None
            setattr(self, field, value)
        # Validate required fields
        for field, (typ, info) in self.__fields__.items():
            if info.default is ... and getattr(self, field) is None and not info.nullable:
                raise ValueError(f"Field '{field}' is required and not nullable")

    def dict(self, *, exclude_none: bool = False) -> Dict[str, Any]:
        result = {}
        for field, (typ, info) in self.__fields__.items():
            value = getattr(self, field)
            if exclude_none and value is None:
                continue
            result[field] = value
        return result

    def json(self, *, exclude_none: bool = False) -> str:
        return json.dumps(self.dict(exclude_none=exclude_none))

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        # For API compatibility; returns a dict describing the fields
        return {
            "title": cls.__name__,
            "type": "object",
            "properties": {
                field: {"type": _python_type_to_json_type(typ)}
                for field, (typ, info) in cls.__fields__.items()
            },
            "required": [
                field
                for field, (typ, info) in cls.__fields__.items()
                if info.default is ...
            ],
        }

def _python_type_to_json_type(typ):
    if typ in (int, float):
        return "number"
    elif typ is str:
        return "string"
    elif typ is bool:
        return "boolean"
    elif typ is dict:
        return "object"
    elif typ is list:
        return "array"
    else:
        return "string"

# --- Engine ---
class Engine:
    def __init__(self, url: str):
        self.url = url
        self._conn_lock = threading.Lock()
        self._conn = None

    def connect(self):
        with self._conn_lock:
            if self._conn is None:
                if self.url.startswith("sqlite:///"):
                    db_path = self.url.replace("sqlite:///", "")
                else:
                    db_path = self.url
                self._conn = sqlite3.connect(db_path, check_same_thread=False)
                self._conn.row_factory = sqlite3.Row
            return self._conn

    def execute(self, sql: str, params=None):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(sql, params or [])
        return cur

def create_engine(url: str) -> Engine:
    return Engine(url)

# --- Session ---
class Session:
    def __init__(self, engine: Engine):
        self.engine = engine
        self._new = []
        self._committed = False

    def add(self, obj: SQLModel):
        self._new.append(obj)

    def commit(self):
        for obj in self._new:
            self._insert(obj)
        self._new.clear()
        self._committed = True

    def refresh(self, obj: SQLModel):
        pk_fields = obj.__primary_keys__
        if not pk_fields:
            raise ValueError("No primary key defined")
        table = obj.__tablename__
        where = " AND ".join(
            f"{pk}=?" for pk in pk_fields
        )
        values = [getattr(obj, pk) for pk in pk_fields]
        sql = f"SELECT * FROM {table} WHERE {where} LIMIT 1"
        cur = self.engine.execute(sql, values)
        row = cur.fetchone()
        if row:
            for field in obj.__fields__:
                setattr(obj, field, row[field])

    def exec(self, statement):
        # statement is a Select object
        sql, params, model_cls = statement._compile()
        cur = self.engine.execute(sql, params)
        results = []
        for row in cur.fetchall():
            obj = model_cls(**dict(row))
            results.append(obj)
        return Result(results)

    def _insert(self, obj: SQLModel):
        table = obj.__tablename__
        fields = []
        values = []
        placeholders = []
        for field, (typ, info) in obj.__fields__.items():
            value = getattr(obj, field)
            if value is None and info.default is not ...:
                value = info.default
            fields.append(field)
            values.append(value)
            placeholders.append("?")
        sql = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
        self.engine.execute(sql, values)
        self.engine.connect().commit()

    def close(self):
        pass

# --- Result ---
class Result:
    def __init__(self, results: List[SQLModel]):
        self._results = results

    def all(self):
        return self._results

    def first(self):
        return self._results[0] if self._results else None

# --- Table creation ---
def SQLModel_create_table(model: Type[SQLModel], engine: Engine):
    table = model.__tablename__
    columns = []
    for field, (typ, info) in model.__fields__.items():
        col_type = _python_type_to_sqlite_type(typ)
        col_def = f"{field} {col_type}"
        if info.primary_key:
            col_def += " PRIMARY KEY"
        if info.nullable or info.default is not ...:
            col_def += " NULL"
        else:
            col_def += " NOT NULL"
        columns.append(col_def)
    sql = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(columns)})"
    engine.execute(sql)
    engine.connect().commit()

def _python_type_to_sqlite_type(typ):
    if typ is int:
        return "INTEGER"
    elif typ is float:
        return "REAL"
    elif typ is str:
        return "TEXT"
    elif typ is bool:
        return "INTEGER"
    else:
        return "TEXT"

def create_all(engine: Engine, models: List[Type[SQLModel]]):
    for model in models:
        SQLModel_create_table(model, engine)

# --- Select ---
class Select:
    def __init__(self, model: Type[SQLModel]):
        self.model = model
        self._where = []
        self._params = []

    def where(self, *conditions):
        for cond in conditions:
            sql, param = _parse_condition(cond)
            self._where.append(sql)
            self._params.append(param)
        return self

    def _compile(self):
        table = self.model.__tablename__
        sql = f"SELECT * FROM {table}"
        params = []
        if self._where:
            sql += " WHERE " + " AND ".join(self._where)
            params = self._params
        return sql, params, self.model

def select(model: Type[SQLModel]) -> Select:
    return Select(model)

def _parse_condition(cond):
    # cond is usually a binary expression like Model.field == value
    # We'll support only simple cases: lambda or custom objects
    # For compatibility, we expect cond to be a BinaryExpression
    if isinstance(cond, BinaryExpression):
        return f"{cond.left} {cond.op} ?", cond.right
    else:
        raise ValueError("Unsupported condition type")

# --- BinaryExpression for where clauses ---
class BinaryExpression:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

def _make_comparison(field_name, op):
    def comparator(self, other):
        return BinaryExpression(field_name, op, other)
    return comparator

# Patch SQLModel fields to support ==, !=, >, <, etc.
def _patch_model_fields(model_cls):
    for field in model_cls.__fields__:
        def make_property(field_name):
            class FieldComparator:
                def __eq__(self, other):
                    return BinaryExpression(field_name, "=", other)
                def __ne__(self, other):
                    return BinaryExpression(field_name, "<>", other)
                def __gt__(self, other):
                    return BinaryExpression(field_name, ">", other)
                def __lt__(self, other):
                    return BinaryExpression(field_name, "<", other)
                def __ge__(self, other):
                    return BinaryExpression(field_name, ">=", other)
                def __le__(self, other):
                    return BinaryExpression(field_name, "<=", other)
            return FieldComparator()
        setattr(model_cls, field, make_property(field))
    return model_cls

# Patch all SQLModel subclasses on import
import sys
def _patch_all_models():
    for name, obj in sys.modules[__name__].__dict__.items():
        if isinstance(obj, type) and issubclass(obj, SQLModel) and obj is not SQLModel:
            _patch_model_fields(obj)
_patch_all_models()

# --- API ---
__all__ = [
    "SQLModel",
    "Field",
    "select",
    "Relationship",
    "Session",
    "create_engine",
    "create_all",
]