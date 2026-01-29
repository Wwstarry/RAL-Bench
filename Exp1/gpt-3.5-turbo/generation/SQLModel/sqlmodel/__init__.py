import typing as t
import json
import threading

# Simple in-memory "database" engine
class Engine:
    def __init__(self):
        # tables: dict[str, dict[int, dict]] - table name -> pk -> row dict
        self.tables = {}
        self.lock = threading.RLock()

    def create_all(self, metadata):
        with self.lock:
            for table_name, table in metadata.tables.items():
                if table_name not in self.tables:
                    self.tables[table_name] = {}

    def drop_all(self, metadata):
        with self.lock:
            for table_name in metadata.tables.keys():
                if table_name in self.tables:
                    del self.tables[table_name]

# Metadata and Table representation
class MetaData:
    def __init__(self):
        self.tables = {}

class Table:
    def __init__(self, name, columns, primary_key):
        self.name = name
        self.columns = columns  # dict[str, Column]
        self.primary_key = primary_key

class Column:
    def __init__(self, name, type_, primary_key=False, default=None, nullable=True):
        self.name = name
        self.type_ = type_
        self.primary_key = primary_key
        self.default = default
        self.nullable = nullable

# Field function to specify metadata on model fields
class FieldInfo:
    def __init__(self, default=t._SpecialForm, *, primary_key=False, default_factory=None, nullable=True):
        self.default = default
        self.primary_key = primary_key
        self.default_factory = default_factory
        self.nullable = nullable

def Field(default=t._SpecialForm, *, primary_key=False, default_factory=None, nullable=True):
    if default is not t._SpecialForm and default_factory is not None:
        raise ValueError("cannot specify both default and default_factory")
    if default is t._SpecialForm and default_factory is None:
        default = None
    return FieldInfo(default=default, primary_key=primary_key, default_factory=default_factory, nullable=nullable)

# Relationship placeholder (not implemented fully, but exposed)
def Relationship(*args, **kwargs):
    # For compatibility, no-op
    return None

# Base class for SQLModel
class SQLModelMeta(type):
    def __new__(cls, name, bases, namespace, **kwargs):
        annotations = namespace.get('__annotations__', {})
        fields = {}
        primary_key = None
        for base in bases:
            if hasattr(base, '__fields__'):
                fields.update(base.__fields__)
        # Collect fields from annotations and FieldInfo
        for field_name, field_type in annotations.items():
            default = namespace.get(field_name, t._SpecialForm)
            if isinstance(default, FieldInfo):
                fi = default
                default_value = fi.default if fi.default is not t._SpecialForm else None
                fields[field_name] = {
                    'type': field_type,
                    'primary_key': fi.primary_key,
                    'default': default_value,
                    'default_factory': fi.default_factory,
                    'nullable': fi.nullable,
                }
                if fi.primary_key:
                    if primary_key is not None:
                        raise RuntimeError("Multiple primary keys not supported")
                    primary_key = field_name
                # Remove from namespace to avoid class attribute shadowing
                if field_name in namespace:
                    del namespace[field_name]
            else:
                # default is a value or t._SpecialForm (no default)
                fields[field_name] = {
                    'type': field_type,
                    'primary_key': False,
                    'default': default if default is not t._SpecialForm else None,
                    'default_factory': None,
                    'nullable': True,
                }
        namespace['__fields__'] = fields
        namespace['__primary_key__'] = primary_key
        # Table name defaults to class name lowercased
        if '__tablename__' not in namespace:
            namespace['__tablename__'] = name.lower()
        # Metadata class attribute (shared)
        if not hasattr(cls, '_metadata'):
            cls._metadata = MetaData()
        # Register table in metadata
        columns = {}
        for fname, finfo in fields.items():
            col = Column(
                name=fname,
                type_=finfo['type'],
                primary_key=finfo['primary_key'],
                default=finfo['default'],
                nullable=finfo['nullable'],
            )
            columns[fname] = col
        table = Table(namespace['__tablename__'], columns, primary_key)
        cls._metadata.tables[namespace['__tablename__']] = table
        return super().__new__(cls, name, bases, namespace)

class SQLModel(metaclass=SQLModelMeta):
    __fields__: t.ClassVar[t.Dict[str, t.Dict[str, t.Any]]]
    __primary_key__: t.ClassVar[t.Optional[str]]
    __tablename__: t.ClassVar[str]

    def __init__(self, **data):
        for fname, finfo in self.__fields__.items():
            if fname in data:
                value = data[fname]
            else:
                if finfo['default_factory'] is not None:
                    value = finfo['default_factory']()
                else:
                    value = finfo['default']
            setattr(self, fname, value)

    def dict(self, *, include=None, exclude=None):
        result = {}
        for fname in self.__fields__:
            if include is not None and fname not in include:
                continue
            if exclude is not None and fname in exclude:
                continue
            result[fname] = getattr(self, fname)
        return result

    def json(self, *, include=None, exclude=None):
        return json.dumps(self.dict(include=include, exclude=exclude))

    @classmethod
    def metadata(cls):
        return cls._metadata

# Select construct
class Select:
    def __init__(self, model):
        self.model = model
        self._where = None

    def where(self, condition):
        self._where = condition
        return self

def select(model):
    return Select(model)

# Session class
class Session:
    def __init__(self, engine):
        self.engine = engine
        self._new = []  # list of instances to add
        self._dirty = set()  # instances modified
        self._identity_map = {}  # (class, pk) -> instance
        self._lock = threading.RLock()

    def add(self, instance):
        with self._lock:
            self._new.append(instance)

    def commit(self):
        with self._lock:
            # Insert new objects
            for obj in self._new:
                self._insert(obj)
            self._new.clear()
            # For this simple ORM, no update tracking implemented
            # Refresh identity map
            self._identity_map.clear()

    def _insert(self, obj):
        table = self.engine.tables.get(obj.__tablename__)
        if table is None:
            raise RuntimeError(f"Table {obj.__tablename__} does not exist in engine")
        pk_name = obj.__primary_key__
        if pk_name is None:
            raise RuntimeError("No primary key defined")
        pk_value = getattr(obj, pk_name)
        if pk_value is None:
            # Auto-generate integer PK if int type
            col = obj.__fields__[pk_name]
            if col['type'] == int:
                pk_value = self._generate_pk(table)
                setattr(obj, pk_name, pk_value)
            else:
                raise RuntimeError("Primary key value is None and cannot be auto-generated")
        if pk_value in table:
            raise RuntimeError(f"Duplicate primary key value {pk_value} for table {obj.__tablename__}")
        # Store row as dict of field values
        row = {}
        for fname in obj.__fields__:
            row[fname] = getattr(obj, fname)
        table[pk_value] = row

    def _generate_pk(self, table):
        if not table:
            return 1
        return max(table.keys()) + 1

    def refresh(self, instance):
        with self._lock:
            table = self.engine.tables.get(instance.__tablename__)
            if table is None:
                raise RuntimeError(f"Table {instance.__tablename__} does not exist")
            pk_name = instance.__primary_key__
            if pk_name is None:
                raise RuntimeError("No primary key defined")
            pk_value = getattr(instance, pk_name)
            if pk_value is None:
                raise RuntimeError("Instance primary key is None")
            row = table.get(pk_value)
            if row is None:
                raise RuntimeError("Instance not found in database")
            for fname in instance.__fields__:
                setattr(instance, fname, row[fname])

    def query(self, model):
        return Query(self, model)

# Query class
class Query:
    def __init__(self, session, model):
        self.session = session
        self.model = model
        self._filters = []

    def filter(self, *criteria):
        self._filters.extend(criteria)
        return self

    def all(self):
        table = self.session.engine.tables.get(self.model.__tablename__)
        if table is None:
            return []
        results = []
        for row in table.values():
            if self._apply_filters(row):
                obj = self._row_to_obj(row)
                results.append(obj)
        return results

    def first(self):
        table = self.session.engine.tables.get(self.model.__tablename__)
        if table is None:
            return None
        for row in table.values():
            if self._apply_filters(row):
                return self._row_to_obj(row)
        return None

    def _apply_filters(self, row):
        if not self._filters:
            return True
        for f in self._filters:
            if not f(row):
                return False
        return True

    def _row_to_obj(self, row):
        obj = self.model()
        for fname in self.model.__fields__:
            setattr(obj, fname, row[fname])
        return obj

# Expression helpers for filtering
def _make_filter(field_name, op, value):
    def f(row):
        lhs = row.get(field_name)
        rhs = value
        if op == '==':
            return lhs == rhs
        elif op == '!=':
            return lhs != rhs
        elif op == '<':
            return lhs < rhs
        elif op == '<=':
            return lhs <= rhs
        elif op == '>':
            return lhs > rhs
        elif op == '>=':
            return lhs >= rhs
        else:
            raise RuntimeError(f"Unsupported operator {op}")
    return f

# Support for simple expressions: model.field == value
class FieldExpression:
    def __init__(self, model, field_name):
        self.model = model
        self.field_name = field_name

    def __eq__(self, other):
        return _make_filter(self.field_name, '==', other)

    def __ne__(self, other):
        return _make_filter(self.field_name, '!=', other)

    def __lt__(self, other):
        return _make_filter(self.field_name, '<', other)

    def __le__(self, other):
        return _make_filter(self.field_name, '<=', other)

    def __gt__(self, other):
        return _make_filter(self.field_name, '>', other)

    def __ge__(self, other):
        return _make_filter(self.field_name, '>=', other)

# Patch SQLModel to support attribute access for filtering
def _getattr_for_filter(cls, name):
    if name in cls.__fields__:
        return FieldExpression(cls, name)
    raise AttributeError(f"{cls.__name__} has no attribute {name}")

setattr(SQLModel, '__getattr__', classmethod(_getattr_for_filter))

# Engine factory function
def create_engine():
    return Engine()

# Expose public API
__all__ = [
    "SQLModel",
    "Field",
    "select",
    "Relationship",
    "Session",
    "create_engine",
]