import json
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple, Type, Union, get_args, get_origin

# -----------------------------
# Utilities for typing and validation
# -----------------------------

_MISSING = object()


def _is_optional(t) -> Tuple[bool, Any]:
    origin = get_origin(t)
    if origin is Union:
        args = get_args(t)
        if type(None) in args:
            # Optional[X] where args like (X, NoneType)
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1:
                return True, non_none[0]
            else:
                # Union with None and multiple types
                return True, Union[tuple(non_none)]
    return False, t


def _validate_type(value: Any, expected_type: Any, field_name: str) -> Any:
    if expected_type is Any or expected_type is None:
        return value
    is_opt, inner = _is_optional(expected_type)
    if value is None:
        if is_opt or expected_type is Any:
            return None
        else:
            raise TypeError(f"Field '{field_name}' cannot be None")
    # Handle simple types and Union
    origin = get_origin(inner if is_opt else expected_type)
    expected = inner if is_opt else expected_type

    if origin is Union:
        # Accept if matches any
        for arg in get_args(expected):
            try:
                return _validate_type(value, arg, field_name)
            except Exception:
                continue
        raise TypeError(f"Field '{field_name}' is not of type {expected}")
    # Try simple casting for common primitives
    base_type = expected
    try:
        if isinstance(value, base_type):
            return value
    except Exception:
        # base_type may be typing constructs
        return value

    # Try to cast common primitives
    for t in (int, float, str, bool):
        if base_type is t:
            try:
                # Special handling: bool from str
                if t is bool and isinstance(value, str):
                    lower = value.strip().lower()
                    if lower in ("true", "1", "yes", "y", "t"):
                        return True
                    if lower in ("false", "0", "no", "n", "f"):
                        return False
                    raise ValueError()
                return t(value)
            except Exception:
                raise TypeError(f"Field '{field_name}' expected {t.__name__}, got {type(value).__name__}")
    # Fallback: if can't ensure type, just return as is
    return value


# -----------------------------
# Field and expressions
# -----------------------------

class Condition:
    def __and__(self, other: "Condition") -> "Condition":
        return CombinedCondition(self, other, op="AND")

    def __or__(self, other: "Condition") -> "Condition":
        return CombinedCondition(self, other, op="OR")

    def evaluate(self, row: Dict[str, Any]) -> bool:
        return True


class BinaryCondition(Condition):
    def __init__(self, model: Type["SQLModel"], field_name: str, op: str, value: Any):
        self.model = model
        self.field_name = field_name
        self.op = op
        self.value = value

    def evaluate(self, row: Dict[str, Any]) -> bool:
        left = row.get(self.field_name, None)
        right = self.value
        if self.op == "==":
            return left == right
        if self.op == "!=":
            return left != right
        if self.op == "<":
            try:
                return left < right
            except Exception:
                return False
        if self.op == "<=":
            try:
                return left <= right
            except Exception:
                return False
        if self.op == ">":
            try:
                return left > right
            except Exception:
                return False
        if self.op == ">=":
            try:
                return left >= right
            except Exception:
                return False
        if self.op == "in":
            try:
                return left in right
            except Exception:
                return False
        return False


class CombinedCondition(Condition):
    def __init__(self, left: Condition, right: Condition, op: str):
        self.left = left
        self.right = right
        self.op = op

    def evaluate(self, row: Dict[str, Any]) -> bool:
        if self.op == "AND":
            return self.left.evaluate(row) and self.right.evaluate(row)
        if self.op == "OR":
            return self.left.evaluate(row) or self.right.evaluate(row)
        return False


class FieldRef:
    def __init__(self, model: Type["SQLModel"], name: str):
        self.model = model
        self.name = name

    def __eq__(self, other: Any) -> Condition:
        return BinaryCondition(self.model, self.name, "==", other)

    def __ne__(self, other: Any) -> Condition:
        return BinaryCondition(self.model, self.name, "!=", other)

    def __lt__(self, other: Any) -> Condition:
        return BinaryCondition(self.model, self.name, "<", other)

    def __le__(self, other: Any) -> Condition:
        return BinaryCondition(self.model, self.name, "<=", other)

    def __gt__(self, other: Any) -> Condition:
        return BinaryCondition(self.model, self.name, ">", other)

    def __ge__(self, other: Any) -> Condition:
        return BinaryCondition(self.model, self.name, ">=", other)

    def in_(self, values: Iterable[Any]) -> Condition:
        return BinaryCondition(self.model, self.name, "in", list(values))


class FieldInfo:
    def __init__(
        self,
        default: Any = _MISSING,
        *,
        default_factory: Optional[Callable[[], Any]] = None,
        primary_key: bool = False,
        nullable: Optional[bool] = None,
        index: bool = False,
        description: Optional[str] = None,
    ):
        self.name: Optional[str] = None
        self.default = default
        self.default_factory = default_factory
        self.primary_key = primary_key
        self.nullable = nullable
        self.index = index
        self.description = description
        self.model: Optional[Type["SQLModel"]] = None
        self.type_: Any = Any

    def __set_name__(self, owner, name):
        self.name = name
        self.model = owner

    def __get__(self, instance, owner):
        if instance is None:
            # Accessed on class, return reference for building expressions
            return FieldRef(owner, self.name or "")
        return instance.__dict__.get(self.name, self._get_default_value())

    def __set__(self, instance, value):
        if self.name is None:
            raise AttributeError("Field not bound to a class")
        expected_type = self.type_
        try:
            value = _validate_type(value, expected_type, self.name)
        except Exception as e:
            raise e
        instance.__dict__[self.name] = value

    def _get_default_value(self):
        if self.default is not _MISSING:
            return self.default
        if self.default_factory is not None:
            try:
                return self.default_factory()
            except Exception:
                return None
        return None


def Field(
    default: Any = _MISSING,
    *,
    default_factory: Optional[Callable[[], Any]] = None,
    primary_key: bool = False,
    nullable: Optional[bool] = None,
    index: bool = False,
    description: Optional[str] = None,
) -> FieldInfo:
    return FieldInfo(
        default,
        default_factory=default_factory,
        primary_key=primary_key,
        nullable=nullable,
        index=index,
        description=description,
    )


# -----------------------------
# Metadata and table info
# -----------------------------

class TableInfo:
    def __init__(self, name: str, model: Type["SQLModel"], columns: Dict[str, FieldInfo], primary_key: Optional[str]):
        self.name = name
        self.model = model
        self.columns = columns
        self.primary_key = primary_key

    def __repr__(self):
        return f"<TableInfo name={self.name!r} pk={self.primary_key!r} columns={list(self.columns.keys())!r}>"


class Metadata:
    def __init__(self):
        self.tables: Dict[str, TableInfo] = {}

    def register(self, table: TableInfo):
        self.tables[table.name] = table

    def create_all(self, engine: "Engine"):
        for name, table in self.tables.items():
            engine._ensure_table(name, table)


# -----------------------------
# Engine and Session
# -----------------------------

class Engine:
    def __init__(self, url: str = ""):
        self.url = url
        # storage: table_name -> list of rows (each row: dict of column -> value)
        self._storage: Dict[str, List[Dict[str, Any]]] = {}
        self._pk_counters: Dict[str, int] = {}
        self._table_infos: Dict[str, TableInfo] = {}

    def _ensure_table(self, name: str, table: TableInfo):
        if name not in self._storage:
            self._storage[name] = []
        if name not in self._pk_counters:
            self._pk_counters[name] = 0
        self._table_infos[name] = table

    def _insert(self, table_name: str, row: Dict[str, Any]) -> Dict[str, Any]:
        table = self._table_infos.get(table_name)
        if not table:
            raise RuntimeError(f"Table {table_name!r} not registered in engine")
        pk = table.primary_key
        if pk:
            if row.get(pk) is None:
                self._pk_counters[table_name] += 1
                row[pk] = self._pk_counters[table_name]
        # For simplicity, append row; if pk exists and matches existing, replace
        if pk:
            existing_idx = None
            for idx, r in enumerate(self._storage[table_name]):
                if r.get(pk) == row.get(pk):
                    existing_idx = idx
                    break
            if existing_idx is None:
                self._storage[table_name].append(dict(row))
            else:
                self._storage[table_name][existing_idx] = dict(row)
        else:
            self._storage[table_name].append(dict(row))
        return row

    def _select_all(self, table_name: str) -> List[Dict[str, Any]]:
        return list(self._storage.get(table_name, []))

    def _find_by_pk(self, table_name: str, pk_name: str, pk_value: Any) -> Optional[Dict[str, Any]]:
        for row in self._storage.get(table_name, []):
            if row.get(pk_name) == pk_value:
                return row
        return None


def create_engine(url: str = "") -> Engine:
    return Engine(url=url)


class Select:
    def __init__(self, model: Type["SQLModel"]):
        self.model = model
        self._where: Optional[Condition] = None

    def where(self, *conditions: Condition) -> "Select":
        for cond in conditions:
            if self._where is None:
                self._where = cond
            else:
                self._where = CombinedCondition(self._where, cond, op="AND")
        return self


def select(model: Type["SQLModel"]) -> Select:
    return Select(model)


class Result:
    def __init__(self, items: List[Any]):
        self._items = items

    def all(self) -> List[Any]:
        return list(self._items)

    def first(self) -> Optional[Any]:
        return self._items[0] if self._items else None

    def __iter__(self) -> Iterator[Any]:
        return iter(self._items)


class Session:
    def __init__(self, engine: Engine):
        self.engine = engine
        self._pending: List[SQLModel] = []
        self._closed = False

    def add(self, obj: "SQLModel"):
        if self._closed:
            raise RuntimeError("Session is closed")
        self._pending.append(obj)

    def add_all(self, objs: Iterable["SQLModel"]):
        for o in objs:
            self.add(o)

    def commit(self):
        if self._closed:
            raise RuntimeError("Session is closed")
        for obj in self._pending:
            model = type(obj)
            table_name = model.__tablename__
            table = model.__table__
            # Prepare row from object
            row = obj.dict()
            saved = self.engine._insert(table_name, row)
            # Push back any generated values (e.g., PK)
            pk = table.primary_key
            if pk and getattr(obj, pk, None) != saved.get(pk):
                setattr(obj, pk, saved.get(pk))
        self._pending.clear()

    def refresh(self, obj: "SQLModel"):
        model = type(obj)
        table_name = model.__tablename__
        table = model.__table__
        pk = table.primary_key
        if not pk:
            return
        pk_value = getattr(obj, pk, None)
        if pk_value is None:
            return
        row = self.engine._find_by_pk(table_name, pk, pk_value)
        if row is None:
            return
        # Update object's fields from row
        for fname in model.__fields__.keys():
            setattr(obj, fname, row.get(fname))

    def get(self, model: Type["SQLModel"], pk_value: Any) -> Optional["SQLModel"]:
        table = model.__table__
        pk = table.primary_key
        if not pk:
            return None
        row = self.engine._find_by_pk(model.__tablename__, pk, pk_value)
        if row is None:
            return None
        return model(**row)

    def exec(self, statement: Select) -> Result:
        if not isinstance(statement, Select):
            raise TypeError("Session.exec expects a Select statement")
        model = statement.model
        table_name = model.__tablename__
        rows = self.engine._select_all(table_name)
        items: List[SQLModel] = []
        for row in rows:
            if statement._where is not None:
                if not statement._where.evaluate(row):
                    continue
            # Build instance
            inst = model(**row)
            items.append(inst)
        return Result(items)

    def close(self):
        self._closed = True

    def __enter__(self) -> "Session":
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc is None:
                # Auto-commit similar to some patterns (but SQLModel doesn't auto-commit)
                pass
        finally:
            self.close()


# -----------------------------
# SQLModel base and metaclass
# -----------------------------

class SQLModelMeta(type):
    def __new__(mcls, name, bases, namespace, **kwargs):
        table_flag = kwargs.pop("table", False)
        cls = super().__new__(mcls, name, bases, dict(namespace))

        # Inherit metadata and fields from bases if available
        annotations: Dict[str, Any] = {}
        # Merge annotations from bases
        for base in reversed(bases):
            base_ann = getattr(base, "__annotations__", {})
            annotations.update(dict(base_ann))
        annotations.update(namespace.get("__annotations__", {}))

        # Prepare fields
        fields: Dict[str, FieldInfo] = {}
        defaults = {k: namespace[k] for k in namespace.keys() if not k.startswith("__")}
        for fname, ftype in annotations.items():
            # Skip ClassVar or others not intended
            if fname.startswith("_"):
                continue
            fi = namespace.get(fname, None)
            if isinstance(fi, FieldInfo):
                field_info = fi
            else:
                # If default assigned directly e.g., x: int = 3
                default_val = defaults.get(fname, _MISSING)
                field_info = FieldInfo(default=default_val)
                setattr(cls, fname, field_info)
            # Bind type information
            field_info.type_ = ftype
            fields[fname] = field_info

        # Determine table name
        tablename = namespace.get("__tablename__", name.lower())

        # Determine primary key
        primary_key_name = None
        for fname, finfo in fields.items():
            if finfo.primary_key:
                primary_key_name = fname
                break
        # If not provided, but there is 'id' field, consider as primary key if Optional[int]
        if primary_key_name is None and "id" in fields:
            fields["id"].primary_key = True
            primary_key_name = "id"

        # Attach class attributes
        setattr(cls, "__fields__", fields)
        setattr(cls, "__tablename__", tablename)

        # Ensure the FieldInfo descriptors know their owner/name
        for fname, finfo in fields.items():
            finfo.__set_name__(cls, fname)

        # Prepare table metadata if table=True
        table_info = TableInfo(tablename, cls, fields, primary_key_name)
        setattr(cls, "__table__", table_info)

        # Attach/reuse metadata registry
        # Use a shared Metadata under the root SQLModel class
        base_with_metadata = None
        for b in bases:
            if hasattr(b, "metadata"):
                base_with_metadata = b
                break
        if base_with_metadata is None:
            # Root class, initialize metadata
            setattr(cls, "metadata", Metadata())
        else:
            # Inherit the same metadata object
            setattr(cls, "metadata", base_with_metadata.metadata)

        # If this is a table model, register it
        # We don't register the base SQLModel itself (no fields)
        if table_flag and name != "SQLModel":
            cls.metadata.register(table_info)

        # Provide model-like methods if not present
        return cls

    def __call__(cls, *args, **kwargs):
        # Standard instantiation
        return super().__call__(*args, **kwargs)


class SQLModel(metaclass=SQLModelMeta):
    def __init__(self, **data):
        # Populate fields with validation
        for fname, finfo in self.__fields__.items():
            if fname in data:
                value = data[fname]
            else:
                if finfo.default is not _MISSING:
                    value = finfo.default
                elif finfo.default_factory is not None:
                    try:
                        value = finfo.default_factory()
                    except Exception:
                        value = None
                else:
                    value = None
            # Validate and assign
            setattr(self, fname, value)

        # Detect unknown fields
        for key in data.keys():
            if key not in self.__fields__:
                # Allow extra fields to be set as attributes for leniency
                setattr(self, key, data[key])

    def dict(self, *, exclude_none: bool = False) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        for fname in self.__fields__.keys():
            val = getattr(self, fname, None)
            if exclude_none and val is None:
                continue
            d[fname] = val
        return d

    def json(self, *, exclude_none: bool = False) -> str:
        return json.dumps(self.dict(exclude_none=exclude_none))

    def __repr__(self):
        field_parts = ", ".join(f"{k}={getattr(self, k, None)!r}" for k in self.__fields__.keys())
        return f"{self.__class__.__name__}({field_parts})"


# -----------------------------
# Relationship placeholder (if required by tests)
# -----------------------------

def Relationship(
    *,
    back_populates: Optional[str] = None,
    sa_relationship_kwargs: Optional[Dict[str, Any]] = None,
) -> Any:
    # Placeholder for compatibility; returns None or empty list depending on context.
    # Since this simplified ORM does not implement relations, we return None.
    return None


# Explicitly export main API components
__all__ = [
    "SQLModel",
    "Field",
    "select",
    "Relationship",
    "Session",
    "create_engine",
]