from typing import Any, Optional, Type, TypeVar, Generic, List, Dict, Union
from typing import get_type_hints, get_origin, get_args
from dataclasses import dataclass, field as dataclass_field, fields as dataclass_fields, asdict
from pydantic import BaseModel, create_model, Field as PydanticField
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime

__version__ = "0.0.1"

T = TypeVar('T')

# Field function - wraps Pydantic Field
def Field(
    default: Any = ...,
    default_factory: Optional[Any] = None,
    primary_key: bool = False,
    foreign_key: Optional[str] = None,
    index: bool = False,
    unique: bool = False,
    nullable: bool = True,
    **kwargs
) -> Any:
    """Create a field with SQLModel-specific metadata."""
    pydantic_kwargs = {
        'default': default if default is not ... else ...,
        **kwargs
    }
    
    if default_factory is not None:
        pydantic_kwargs['default_factory'] = default_factory
    
    field_info = PydanticField(**pydantic_kwargs)
    field_info.metadata = field_info.metadata or []
    
    # Store SQLModel-specific metadata
    if isinstance(field_info.metadata, list):
        field_info.metadata.append({
            'primary_key': primary_key,
            'foreign_key': foreign_key,
            'index': index,
            'unique': unique,
            'nullable': nullable,
        })
    
    return field_info


class SQLModelMetaclass(type):
    """Metaclass for SQLModel to handle table creation and ORM behavior."""
    
    def __new__(mcs, name: str, bases: tuple, namespace: dict, **kwargs):
        # Extract table configuration
        table_name = kwargs.get('table', None)
        
        # Create the class
        cls = super().__new__(mcs, name, bases, namespace)
        
        # Store table metadata
        cls.__table_name__ = table_name or name.lower()
        cls.__fields_metadata__ = {}
        cls.__primary_key__ = None
        
        # Process fields from annotations
        if hasattr(cls, '__annotations__'):
            for field_name, field_type in cls.__annotations__.items():
                if field_name.startswith('_'):
                    continue
                
                # Get field info from class attributes
                field_value = getattr(cls, field_name, None)
                
                metadata = {
                    'type': field_type,
                    'primary_key': False,
                    'foreign_key': None,
                    'index': False,
                    'unique': False,
                    'nullable': True,
                    'default': None,
                }
                
                # Extract metadata from Pydantic Field
                if hasattr(field_value, 'metadata') and field_value.metadata:
                    for meta_item in field_value.metadata:
                        if isinstance(meta_item, dict):
                            metadata.update(meta_item)
                
                # Check for default value
                if field_value is not None and not isinstance(field_value, type(PydanticField())):
                    metadata['default'] = field_value
                elif hasattr(field_value, 'default') and field_value.default is not ...:
                    metadata['default'] = field_value.default
                
                cls.__fields_metadata__[field_name] = metadata
                
                if metadata['primary_key']:
                    cls.__primary_key__ = field_name
        
        return cls


class SQLModel(BaseModel, metaclass=SQLModelMetaclass):
    """Base class for SQLModel models combining Pydantic and ORM capabilities."""
    
    model_config = {'from_attributes': True}
    
    def __init__(self, **data):
        super().__init__(**data)
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Return model as dictionary."""
        return self.model_dump(**kwargs)
    
    def json(self, **kwargs) -> str:
        """Return model as JSON string."""
        return self.model_dump_json(**kwargs)


class SelectStatement(Generic[T]):
    """Represents a SELECT statement."""
    
    def __init__(self, model: Type[T]):
        self.model = model
        self.filters: List[tuple] = []
        self.limit_value: Optional[int] = None
        self.offset_value: Optional[int] = None
    
    def where(self, condition: Any) -> 'SelectStatement[T]':
        """Add a WHERE clause."""
        self.filters.append(condition)
        return self
    
    def limit(self, limit: int) -> 'SelectStatement[T]':
        """Add a LIMIT clause."""
        self.limit_value = limit
        return self
    
    def offset(self, offset: int) -> 'SelectStatement[T]':
        """Add an OFFSET clause."""
        self.offset_value = offset
        return self


def select(model: Type[T]) -> SelectStatement[T]:
    """Create a SELECT statement."""
    return SelectStatement(model)


class Engine:
    """Database engine for SQLite."""
    
    def __init__(self, url: str):
        self.url = url
        # Extract database path from URL
        if url.startswith('sqlite:///'):
            self.db_path = url.replace('sqlite:///', '')
        elif url.startswith('sqlite://'):
            self.db_path = url.replace('sqlite://', '')
        else:
            self.db_path = url
        
        self.connection = None
    
    def connect(self):
        """Create a database connection."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()


class Session:
    """Database session for ORM operations."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.connection = engine.connect()
        self.cursor = self.connection.cursor()
        self._identity_map: Dict[tuple, Any] = {}
    
    def add(self, obj: SQLModel) -> None:
        """Add an object to the session."""
        # Mark for insertion
        if not hasattr(obj, '_session_state'):
            obj._session_state = {'new': True, 'dirty': False}
    
    def commit(self) -> None:
        """Commit all pending changes."""
        self.connection.commit()
    
    def refresh(self, obj: SQLModel) -> None:
        """Refresh an object from the database."""
        if not hasattr(obj, '__table_name__'):
            return
        
        pk_field = obj.__primary_key__
        if not pk_field:
            return
        
        pk_value = getattr(obj, pk_field)
        
        query = f"SELECT * FROM {obj.__table_name__} WHERE {pk_field} = ?"
        self.cursor.execute(query, (pk_value,))
        row = self.cursor.fetchone()
        
        if row:
            row_dict = dict(row)
            for key, value in row_dict.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
    
    def exec(self, statement: Union[SelectStatement, str], params: tuple = ()) -> 'Result':
        """Execute a statement."""
        if isinstance(statement, SelectStatement):
            return self._execute_select(statement)
        else:
            self.cursor.execute(statement, params)
            return Result(self.cursor)
    
    def _execute_select(self, statement: SelectStatement) -> 'Result':
        """Execute a SELECT statement."""
        model = statement.model
        table_name = model.__table_name__
        
        query = f"SELECT * FROM {table_name}"
        params = []
        
        if statement.filters:
            where_clauses = []
            for filter_item in statement.filters:
                if isinstance(filter_item, tuple) and len(filter_item) == 3:
                    field, op, value = filter_item
                    where_clauses.append(f"{field} {op} ?")
                    params.append(value)
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
        
        if statement.limit_value is not None:
            query += f" LIMIT {statement.limit_value}"
        
        if statement.offset_value is not None:
            query += f" OFFSET {statement.offset_value}"
        
        self.cursor.execute(query, params)
        return Result(self.cursor, model)
    
    def close(self) -> None:
        """Close the session."""
        self.cursor.close()
        self.connection.close()


class Result:
    """Result set from a query."""
    
    def __init__(self, cursor: sqlite3.Cursor, model: Optional[Type[SQLModel]] = None):
        self.cursor = cursor
        self.model = model
        self._rows = None
    
    def all(self) -> List[Any]:
        """Get all results."""
        rows = self.cursor.fetchall()
        if self.model:
            return [self.model(**dict(row)) for row in rows]
        return [dict(row) for row in rows]
    
    def first(self) -> Optional[Any]:
        """Get the first result."""
        row = self.cursor.fetchone()
        if row is None:
            return None
        if self.model:
            return self.model(**dict(row))
        return dict(row)
    
    def scalars(self) -> 'ScalarResult':
        """Get scalar results."""
        return ScalarResult(self.cursor, self.model)


class ScalarResult:
    """Scalar result set from a query."""
    
    def __init__(self, cursor: sqlite3.Cursor, model: Optional[Type[SQLModel]] = None):
        self.cursor = cursor
        self.model = model
    
    def all(self) -> List[Any]:
        """Get all scalar results."""
        rows = self.cursor.fetchall()
        if self.model:
            return [self.model(**dict(row)) for row in rows]
        return [row[0] if row else None for row in rows]
    
    def first(self) -> Optional[Any]:
        """Get the first scalar result."""
        row = self.cursor.fetchone()
        if row is None:
            return None
        if self.model:
            return self.model(**dict(row))
        return row[0] if row else None


def create_engine(url: str) -> Engine:
    """Create a database engine."""
    return Engine(url)


@contextmanager
def session_context(engine: Engine):
    """Context manager for database sessions."""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def create_all(engine: Engine, models: List[Type[SQLModel]]) -> None:
    """Create all tables for the given models."""
    conn = engine.connect()
    cursor = conn.cursor()
    
    for model in models:
        if not hasattr(model, '__table_name__'):
            continue
        
        table_name = model.__table_name__
        fields_metadata = model.__fields_metadata__
        
        columns = []
        for field_name, metadata in fields_metadata.items():
            col_def = _build_column_definition(field_name, metadata)
            columns.append(col_def)
        
        if not columns:
            continue
        
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
        
        try:
            cursor.execute(create_table_sql)
        except sqlite3.OperationalError:
            pass
    
    conn.commit()
    conn.close()


def _build_column_definition(field_name: str, metadata: Dict[str, Any]) -> str:
    """Build a SQL column definition."""
    field_type = metadata['type']
    
    # Map Python types to SQL types
    sql_type = _python_type_to_sql(field_type)
    
    col_def = f"{field_name} {sql_type}"
    
    if metadata.get('primary_key'):
        col_def += " PRIMARY KEY"
    
    if metadata.get('unique'):
        col_def += " UNIQUE"
    
    if not metadata.get('nullable') and not metadata.get('primary_key'):
        col_def += " NOT NULL"
    
    if metadata.get('default') is not None:
        default_val = metadata['default']
        if isinstance(default_val, str):
            col_def += f" DEFAULT '{default_val}'"
        else:
            col_def += f" DEFAULT {default_val}"
    
    return col_def


def _python_type_to_sql(python_type: Any) -> str:
    """Convert Python type to SQL type."""
    # Handle Optional types
    origin = get_origin(python_type)
    if origin is Union:
        args = get_args(python_type)
        # Filter out NoneType
        non_none_args = [arg for arg in args if arg is not type(None)]
        if non_none_args:
            python_type = non_none_args[0]
    
    if python_type is int or python_type == int:
        return "INTEGER"
    elif python_type is str or python_type == str:
        return "TEXT"
    elif python_type is float or python_type == float:
        return "REAL"
    elif python_type is bool or python_type == bool:
        return "INTEGER"
    elif python_type is datetime or python_type == datetime:
        return "TEXT"
    else:
        return "TEXT"


__all__ = [
    'SQLModel',
    'Field',
    'select',
    'Session',
    'create_engine',
    'create_all',
    'session_context',
]