import sqlite3
import json
from typing import Any, Dict, List, Optional, Type, Union, get_type_hints

# A simple mapping of Python types to SQLite column types
_SQLITE_TYPE_MAP = {
    int: "INTEGER",
    float: "REAL",
    bool: "BOOLEAN",
    str: "TEXT",
}

def _python_type_to_sqlite(python_type):
    # Fallback for unrecognized types
    return _SQLITE_TYPE_MAP.get(python_type, "TEXT")

class FieldInfo:
    __slots__ = (
        "default",
        "primary_key",
        "nullable",
        "index",
        "extra"
    )
    def __init__(self, default, primary_key, nullable, index, **extra):
        self.default = default
        self.primary_key = primary_key
        self.nullable = nullable
        self.index = index
        self.extra = extra


def Field(
    default=...,
    *,
    primary_key: bool = False,
    nullable: bool = True,
    index: bool = False,
    **extra
) -> Any:
    """
    Mimic pydantic's Field but store ORM-related info.
    """
    return FieldInfo(default, primary_key, nullable, index, **extra)


def Relationship(*args, **kwargs):
    """
    Placeholder for relationship support if required.
    """
    # For now, return None or some placeholder
    return None


class _TableMetadata:
    """
    Metadata holder for a given Table (class).
    Stores field definitions and creates the table in the DB.
    """
    def __init__(self, model_cls):
        self.model_cls = model_cls
        self.fields = []
        self.pk_name = None
        self.table_name = model_cls.__name__
        self.collect_fields()

    def collect_fields(self):
        # Use the model's __fields__ to populate self.fields
        # Each entry: (field_name, col_name, FieldInfo, python_type)
        cls = self.model_cls
        for name, field_info in cls.__fields__.items():
            python_type = field_info.extra.get("annotation", Any)
            is_pk = field_info.primary_key
            if is_pk:
                self.pk_name = name
            self.fields.append((name, name, field_info, python_type))

    def create_table_sql(self):
        """
        Build a CREATE TABLE statement for this model.
        """
        cols = []
        for field_name, col_name, field_info, py_type in self.fields:
            col_type = _python_type_to_sqlite(py_type)
            col_def = f'"{col_name}" {col_type}'
            if field_info.primary_key:
                col_def += " PRIMARY KEY AUTOINCREMENT"
            elif not field_info.nullable:
                col_def += " NOT NULL"
            cols.append(col_def)
        col_defs_str = ", ".join(cols)
        return f'CREATE TABLE IF NOT EXISTS "{self.table_name}" ({col_defs_str});'


class _SQLModelMetadata:
    """
    Captures all models that declare table=True and can create them.
    """
    def __init__(self):
        self._tables = []

    def register_table(self, model_cls):
        self._tables.append(_TableMetadata(model_cls))

    def create_all(self, engine):
        # For each table, run CREATE TABLE statements
        conn = sqlite3.connect(engine.connection_string)
        try:
            for tbl_meta in self._tables:
                sql = tbl_meta.create_table_sql()
                conn.execute(sql)
        finally:
            conn.commit()
            conn.close()


class SQLModel:
    """
    Base class mimicking SQLModel behavior.
    
    - Provides a place to store metadata.
    - Captures fields from annotations plus Field() definitions
      into a class-level __fields__ dict.
    - If table=True is specified in __init_subclass__, registers in metadata.
    - Provides pydantic-like dict() and json() methods.
    """

    metadata = _SQLModelMetadata()
    __fields__: Dict[str, FieldInfo] = {}

    def __init_subclass__(cls, table: bool = False):
        super().__init_subclass__()
        cls.__fields__ = {}

        # Gather type hints
        hints = get_type_hints(cls, include_extras=True)

        # For each field in annotations, see if a FieldInfo is assigned
        for name, annotation in hints.items():
            field_default = getattr(cls, name, None)
            # Check if it's actually a FieldInfo
            if isinstance(field_default, FieldInfo):
                # Store annotation for later usage
                field_default.extra["annotation"] = annotation
                cls.__fields__[name] = field_default
            else:
                # Possibly no default or a normal default
                fi = FieldInfo(
                    default=field_default if field_default is not None else ...,
                    primary_key=False,
                    nullable=True,
                    index=False,
                    annotation=annotation
                )
                # If the cls has the same name in __dict__, it's a real default
                # otherwise we treat as ...
                if name in cls.__dict__:
                    fi.default = field_default
                else:
                    fi.default = ...
                cls.__fields__[name] = fi

        cls.__table_defined__ = table
        if table:
            # Register table with metadata
            SQLModel.metadata.register_table(cls)

    def __init__(self, **kwargs):
        # Assign values to fields, applying defaults if necessary
        cls = self.__class__
        for name, field_info in cls.__fields__.items():
            if name in kwargs:
                value = kwargs[name]
            else:
                if field_info.default is ...:
                    value = None
                else:
                    value = field_info.default
            setattr(self, name, value)

    def dict(self) -> Dict[str, Any]:
        """
        Return a dict of field values like pydantic's dict().
        """
        cls = self.__class__
        result = {}
        for name, field_info in cls.__fields__.items():
            result[name] = getattr(self, name, None)
        return result

    def json(self) -> str:
        """
        Return a JSON string of the model's dict.
        """
        return json.dumps(self.dict())


def create_engine(connection_string: str, echo: bool = False):
    """
    Mimics create_engine(). We'll store just the connection string.
    """
    engine = Engine(connection_string, echo=echo)
    return engine


class Engine:
    """
    A minimal engine that just holds the connection string
    and echo flag.
    """
    def __init__(self, connection_string, echo=False):
        self.connection_string = connection_string
        self.echo = echo


# Expression and query builder machinery

class BinaryExpression:
    """
    Simple binary expression like Hero.name == "foo".
    We store left (a Column or something) and right (a value),
    plus the operation, e.g. '='.
    """
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"<BinaryExpression {self.left} {self.op} {self.right}>"


class Column:
    """
    Placeholder for model columns, e.g. Hero.name is a Column.
    We store model, column_name, etc. Then __eq__ etc. build BinaryExpression.
    """
    def __init__(self, model_cls, col_name):
        self.model_cls = model_cls
        self.col_name = col_name

    def __eq__(self, other):
        return BinaryExpression(self, "=", other)

    def __ne__(self, other):
        return BinaryExpression(self, "<>", other)

    def __lt__(self, other):
        return BinaryExpression(self, "<", other)

    def __le__(self, other):
        return BinaryExpression(self, "<=", other)

    def __gt__(self, other):
        return BinaryExpression(self, ">", other)

    def __ge__(self, other):
        return BinaryExpression(self, ">=", other)

    def __repr__(self):
        return f"{self.model_cls.__name__}.{self.col_name}"


def select(model_cls):
    """
    Return a Select object for the given model.
    """
    return Select(model_cls)


class Select:
    """
    Minimal select statement object storing model, optional where condition, etc.
    """
    def __init__(self, model_cls):
        self.model_cls = model_cls
        self._where = None

    def where(self, condition):
        self._where = condition
        return self


class Result:
    """
    Holds the rows returned by a session's exec() of a query.
    Allows .all() and .first().
    """
    def __init__(self, rows, model_cls):
        self._rows = rows
        self._model_cls = model_cls

    def all(self):
        return self._rows

    def first(self):
        return self._rows[0] if self._rows else None

    def __iter__(self):
        return iter(self._rows)


def _get_column_expressions(model_cls):
    """
    Build a dict of column_name -> Column objects for all fields.
    This allows e.g. model_cls.name == "foo" to produce a BinaryExpression.
    """
    d = {}
    for field_name in model_cls.__fields__:
        d[field_name] = Column(model_cls, field_name)
    return d


class Session:
    """
    Minimal Session that:
      - holds its own DB connection
      - can add(), commit()
      - can exec(select(...)) queries
      - can refresh() objects
    """
    def __init__(self, engine: Engine):
        self._engine = engine
        self._conn = sqlite3.connect(engine.connection_string)
        self._conn.row_factory = sqlite3.Row
        self._in_memory_objects = []
        # Track new objects to insert on commit
        self._pending_inserts = []

    def add(self, obj: SQLModel):
        """
        Add object to the session to be inserted on commit.
        """
        self._pending_inserts.append(obj)

    def commit(self):
        """
        Insert pending objects, finalize transaction.
        """
        try:
            for obj in self._pending_inserts:
                self._insert_obj(obj)
            self._pending_inserts.clear()
            self._conn.commit()
        except:
            self._conn.rollback()
            raise

    def refresh(self, obj: SQLModel):
        """
        Refresh the object from DB (e.g. update PK if autoincrement).
        We'll fetch the row by PK and set the fields.
        """
        cls = obj.__class__
        meta = None
        for t in SQLModel.metadata._tables:
            if t.model_cls is cls:
                meta = t
                break
        if not meta or not meta.pk_name:
            return
        pk_value = getattr(obj, meta.pk_name, None)
        if pk_value is None:
            return
        table_name = meta.table_name
        sql = f'SELECT * FROM "{table_name}" WHERE "{meta.pk_name}" = ?'
        cur = self._conn.execute(sql, (pk_value,))
        row = cur.fetchone()
        if row:
            # assign fields
            for name, _, field_info, py_type in meta.fields:
                setattr(obj, name, row[name])

    def exec(self, statement: Union[Select, Any]):
        """
        Execute a 'select(...)' or other statement.
        Return a Result object that allows .all() or .first().
        """
        if isinstance(statement, Select):
            return self._exec_select(statement)
        # fallback for raw sql if needed
        return None

    def _exec_select(self, stmt: Select):
        model_cls = stmt.model_cls
        # Find the metadata
        meta = None
        for t in SQLModel.metadata._tables:
            if t.model_cls is model_cls:
                meta = t
                break
        if not meta:
            return Result([], model_cls)

        table_name = meta.table_name
        sql = f'SELECT * FROM "{table_name}"'
        params = []
        if stmt._where is not None:
            w_sql, w_params = self._build_where_sql(stmt._where, meta)
            sql += " WHERE " + w_sql
            params.extend(w_params)

        cur = self._conn.execute(sql, tuple(params))
        rows = cur.fetchall()
        objects = []
        for row in rows:
            obj_kwargs = {}
            for name, _, field_info, py_type in meta.fields:
                obj_kwargs[name] = row[name]
            obj = model_cls(**obj_kwargs)
            objects.append(obj)

        return Result(objects, model_cls)

    def _build_where_sql(self, condition, meta):
        """
        Convert a BinaryExpression or nested condition to a SQL where string
        and parameter list.
        """
        if isinstance(condition, BinaryExpression):
            col_name = condition.left.col_name
            op = condition.op
            val = condition.right
            return f'"{col_name}" {op} ?', [val]
        # if more complex (e.g. AND, OR) were needed, we'd handle it here
        return "1=1", []

    def _insert_obj(self, obj: SQLModel):
        # Insert the object into the DB.
        cls = obj.__class__
        meta = None
        for t in SQLModel.metadata._tables:
            if t.model_cls is cls:
                meta = t
                break
        if not meta:
            return
        table_name = meta.table_name
        field_names = []
        placeholders = []
        values = []
        for (fname, cname, finfo, py_type) in meta.fields:
            if finfo.primary_key and finfo.default is ...:
                # Likely auto-increment, skip from explicit insert
                continue
            field_names.append(cname)
            val = getattr(obj, fname, None)
            placeholders.append("?")
            values.append(val)
        sql_fields = ", ".join(f'"{fn}"' for fn in field_names)
        sql_places = ", ".join(placeholders)
        sql = f'INSERT INTO "{table_name}" ({sql_fields}) VALUES ({sql_places})'
        cur = self._conn.execute(sql, values)
        # If there's an autoincrement PK, update it
        if meta.pk_name:
            pk_field_info = cls.__fields__[meta.pk_name]
            if pk_field_info.primary_key:
                if getattr(obj, meta.pk_name) is None:
                    # fetch last row id
                    new_id = cur.lastrowid
                    setattr(obj, meta.pk_name, new_id)


# Provide a minimal convenience for attribute references, e.g. MyModel.name
# We accomplish this by hooking into __getattr__ on the class if not found.
def __getattr_for_model_cls(cls, name):
    if name in cls.__fields__:
        # Return a Column instance
        return Column(cls, name)
    raise AttributeError(f"type object '{cls.__name__}' has no attribute '{name}'")

SQLModel.__getattr__ = classmethod(__getattr_for_model_cls)