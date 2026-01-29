# file content here
import json
from typing import Any, Optional, Type, Dict, List, Union, get_args, get_origin

# --- Custom Exceptions ---

class NoResultFound(Exception):
    """Raised by Session.exec().one() when no result is found."""
    pass

class MultipleResultsFound(Exception):
    """Raised by Session.exec().one() when multiple results are found."""
    pass

# --- Relationship Marker ---

class RelationshipInfo:
    """A marker class for relationship fields."""
    def __init__(self, back_populates: Optional[str] = None):
        self.back_populates = back_populates

def Relationship(*, back_populates: Optional[str] = None) -> Any:
    """
    A placeholder for defining relationships.
    In this mock, it doesn't perform any logic but allows the attribute to be
    identified by the metaclass.
    """
    return RelationshipInfo(back_populates=back_populates)

# --- Pydantic-like Core ---

class FieldInfo:
    """Holds information about a model field."""
    def __init__(self, default: Any, *, primary_key: bool, nullable: bool):
        self.default = default
        self.primary_key = primary_key
        self.nullable = nullable

def Field(
    default: Any = ...,
    *,
    primary_key: bool = False,
) -> Any:
    """
    Used to provide extra configuration for a field.
    This function actually returns a FieldInfo instance.
    """
    return FieldInfo(default=default, primary_key=primary_key, nullable=default is None)

# --- SQLAlchemy-like Core ---

class MetaData:
    """A container for a collection of Table objects."""
    def __init__(self):
        self.tables: Dict[str, 'Table'] = {}

    def create_all(self, bind: 'Engine'):
        """Creates all tables in the database."""
        bind.create_all(self)

class Column:
    """Represents a column in a database table."""
    def __init__(self, name: str, type_: Type, primary_key: bool = False, nullable: bool = True):
        self.name = name
        self.type = type_
        self.primary_key = primary_key
        self.nullable = nullable

    def __eq__(self, other: Any) -> tuple:
        """Capture equality comparisons for WHERE clauses."""
        return ('eq', self, other)

class Table:
    """Represents a database table."""
    def __init__(self, name: str, metadata: MetaData, *columns: Column):
        self.name = name
        self.metadata = metadata
        self.columns: Dict[str, Column] = {c.name: c for c in columns}
        self.primary_key: List[Column] = [c for c in columns if c.primary_key]
        metadata.tables[name] = self

# --- In-Memory Engine ---

class Engine:
    """A mock database engine that stores data in memory."""
    def __init__(self):
        self._tables: Dict[str, Table] = {}
        self._data: Dict[str, List[Dict[str, Any]]] = {}
        self._pk_counters: Dict[str, int] = {}

    def create_all(self, metadata: MetaData):
        """'Creates' tables by registering them with the engine."""
        for table_name, table_obj in metadata.tables.items():
            if table_name not in self._tables:
                self._tables[table_name] = table_obj
                self._data[table_name] = []
                self._pk_counters[table_name] = 1

    def connect(self):
        """Returns a connection-like object (the engine itself)."""
        return self

def create_engine(url: str, **kwargs: Any) -> Engine:
    """
    Creates a new Engine instance. The URL is ignored in this mock implementation.
    """
    return Engine()

# --- Select Statement Builder ---

class Select:
    """Represents a SQL SELECT statement."""
    def __init__(self, entity: Type['SQLModel']):
        self._entity = entity
        self._where_clauses: List[tuple] = []

    def where(self, *clauses: Any):
        """Adds a WHERE clause to the statement."""
        self._where_clauses.extend(c for c in clauses if c is not None)
        return self

def select(*entities: Type['SQLModel']) -> Select:
    """Creates a new Select statement."""
    if not entities or len(entities) > 1:
        raise NotImplementedError("This mock only supports select(Model)")
    return Select(entities[0])

# --- Query Result ---

class Result:
    """Holds the results of a query execution."""
    def __init__(self, rows: List[Any]):
        self._rows = rows

    def first(self) -> Optional[Any]:
        """Returns the first result, or None if there are no results."""
        return self._rows[0] if self._rows else None

    def all(self) -> List[Any]:
        """Returns all results as a list."""
        return self._rows

    def one(self) -> Any:
        """
        Returns exactly one result, raising an error if there is not exactly one.
        """
        if len(self._rows) == 1:
            return self._rows[0]
        elif len(self._rows) == 0:
            raise NoResultFound("No row was found for one()")
        else:
            raise MultipleResultsFound("Multiple rows were found for one()")

# --- Session ---

class Session:
    """Manages persistence operations for ORM objects."""
    def __init__(self, engine: Engine):
        self._engine = engine
        self._new: List[Any] = []

    def add(self, instance: 'SQLModel'):
        """Places an object in the Session."""
        if instance not in self._new:
            self._new.append(instance)

    def commit(self):
        """Flushes all changes to the 'database'."""
        for instance in self._new:
            table = instance.__table__
            if table is None:
                continue
            table_name = table.name
            table_data = self._engine._data[table_name]
            
            row_data = instance.dict()
            
            if len(table.primary_key) == 1:
                pk_col = table.primary_key[0]
                if row_data.get(pk_col.name) is None:
                    pk_val = self._engine._pk_counters[table_name]
                    row_data[pk_col.name] = pk_val
                    setattr(instance, pk_col.name, pk_val)
                    self._engine._pk_counters[table_name] += 1

            table_data.append(row_data)
        self._new.clear()

    def exec(self, statement: Select) -> Result:
        """Executes a statement and returns a Result object."""
        model_cls = statement._entity
        table_name = model_cls.__table__.name
        
        if table_name not in self._engine._data:
            return Result([])

        all_rows = self._engine._data[table_name]
        
        if not statement._where_clauses:
            filtered_rows = all_rows
        else:
            filtered_rows = []
            for row in all_rows:
                match = True
                for op, column_attr, value in statement._where_clauses:
                    col_name = column_attr.name
                    if op == 'eq':
                        if row.get(col_name) != value:
                            match = False
                            break
                if match:
                    filtered_rows.append(row)
        
        instances = [model_cls(**row) for row in filtered_rows]
        return Result(instances)

    def refresh(self, instance: 'SQLModel'):
        """Expires and reloads the given instance's state from the 'database'."""
        model_cls = type(instance)
        table = model_cls.__table__
        
        if table is None or not table.primary_key:
            raise ValueError("Cannot refresh instance without a primary key")
        
        pk_cols = {c.name: getattr(instance, c.name) for c in table.primary_key}
        if any(v is None for v in pk_cols.values()):
            raise ValueError("Cannot refresh instance with a non-set primary key")

        table_data = self._engine._data[table.name]
        found_row = None
        for row in table_data:
            is_match = all(row.get(pk_name) == pk_val for pk_name, pk_val in pk_cols.items())
            if is_match:
                found_row = row
                break
        
        if found_row is None:
            raise NoResultFound("Instance not found in 'database' for refresh")

        for col_name, value in found_row.items():
            setattr(instance, col_name, value)

# --- SQLModel Core ---

class SQLModelMetaclass(type):
    """Metaclass that combines Pydantic and SQLAlchemy behavior."""
    def __new__(cls, name: str, bases: tuple, dct: dict, **kwargs: Any):
        new_class = super().__new__(cls, name, bases, dct)

        if name == 'SQLModel':
            return new_class

        fields: Dict[str, tuple[Type, FieldInfo]] = {}
        for base in reversed(bases):
            if hasattr(base, '__fields__'):
                fields.update(base.__fields__)

        annotations = dct.get('__annotations__', {})
        
        for field_name, field_type in annotations.items():
            field_value = dct.get(field_name, Field())
            
            field_info = field_value if isinstance(field_value, FieldInfo) else Field(default=field_value)
            
            origin = get_origin(field_type)
            type_args = get_args(field_type)
            is_optional = origin is Union and type(None) in type_args
            
            if is_optional:
                field_info.nullable = True
                actual_type = next(t for t in type_args if t is not type(None))
            else:
                actual_type = field_type
                if field_info.default is None:
                    field_info.nullable = True

            fields[field_name] = (actual_type, field_info)

        new_class.__fields__ = fields

        is_table_arg = kwargs.get('table', False)
        has_pk = any(f_info.primary_key for _, f_info in fields.values())
        
        is_table_model = is_table_arg or has_pk
        
        if not is_table_model:
            new_class.__table__ = None
            return new_class

        table_name = name.lower()
        columns = []
        for field_name, (field_type, field_info) in fields.items():
            if isinstance(dct.get(field_name), RelationshipInfo):
                continue

            col = Column(
                name=field_name,
                type_=field_type,
                primary_key=field_info.primary_key,
                nullable=field_info.nullable
            )
            columns.append(col)
            setattr(new_class, field_name, col)
        
        metadata = getattr(SQLModel, 'metadata', MetaData())
        setattr(SQLModel, 'metadata', metadata)
        new_class.metadata = metadata
        
        new_class.__table__ = Table(table_name, new_class.metadata, *columns)
        
        return new_class

class SQLModel(metaclass=SQLModelMetaclass):
    """Base class for all SQLModel models."""
    metadata = MetaData()
    __table__: Optional[Table] = None
    __fields__: Dict[str, tuple[Type, FieldInfo]] = {}

    def __init__(self, **kwargs: Any):
        for field_name, (field_type, field_info) in self.__class__.__fields__.items():
            value = kwargs.get(field_name, field_info.default)
            
            if value is ...:
                if not field_info.nullable:
                    raise ValueError(f"Field '{field_name}' is required")
                value = None
            
            if value is not None:
                try:
                    if not isinstance(value, field_type):
                        value = field_type(value)
                except (ValueError, TypeError):
                    pass
            
            setattr(self, field_name, value)

    def dict(self) -> Dict[str, Any]:
        """Returns a dictionary representation of the model."""
        d = {}
        for field_name in self.__class__.__fields__:
            if hasattr(self, field_name):
                d[field_name] = getattr(self, field_name)
        return d

    def json(self, **kwargs: Any) -> str:
        """Returns a JSON string representation of the model."""
        return json.dumps(self.dict(), **kwargs)

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={getattr(self, k)!r}" for k in self.__class__.__fields__ if hasattr(self, k))
        return f"{self.__class__.__name__}({attrs})"

    def __setattr__(self, name: str, value: Any):
        object.__setattr__(self, name, value)