"""
Pure Python implementation of SQLModel - API-compatible with the reference implementation.
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    get_type_hints,
    get_origin,
    get_args,
)
from datetime import datetime
import inspect
import sqlite3
from contextlib import contextmanager


# Type variable for generic model
T = TypeVar("T", bound="SQLModel")


class FieldInfo:
    """Represents metadata about a field."""
    
    def __init__(
        self,
        default: Any = None,
        default_factory: Optional[Any] = None,
        primary_key: bool = False,
        nullable: bool = True,
        index: bool = False,
        unique: bool = False,
        sa_column: Any = None,
        **kwargs: Any,
    ):
        self.default = default
        self.default_factory = default_factory
        self.primary_key = primary_key
        self.nullable = nullable
        self.index = index
        self.unique = unique
        self.sa_column = sa_column
        self.extra = kwargs


def Field(
    default: Any = ...,
    *,
    default_factory: Optional[Any] = None,
    primary_key: bool = False,
    nullable: bool = True,
    index: bool = False,
    unique: bool = False,
    sa_column: Any = None,
    **kwargs: Any,
) -> Any:
    """Create a field with metadata."""
    if default is ...:
        default = None
    return FieldInfo(
        default=default,
        default_factory=default_factory,
        primary_key=primary_key,
        nullable=nullable,
        index=index,
        unique=unique,
        sa_column=sa_column,
        **kwargs,
    )


class Relationship:
    """Placeholder for relationship definitions."""
    
    def __init__(self, **kwargs: Any):
        self.kwargs = kwargs


def _python_type_to_sql(python_type: Type) -> str:
    """Convert Python type to SQL type."""
    origin = get_origin(python_type)
    
    # Handle Optional types
    if origin is Union:
        args = get_args(python_type)
        # Filter out NoneType
        non_none_args = [arg for arg in args if arg is not type(None)]
        if non_none_args:
            python_type = non_none_args[0]
    
    if python_type is int:
        return "INTEGER"
    elif python_type is str:
        return "TEXT"
    elif python_type is float:
        return "REAL"
    elif python_type is bool:
        return "INTEGER"  # SQLite uses INTEGER for boolean
    elif python_type is bytes:
        return "BLOB"
    elif python_type is datetime:
        return "TEXT"  # Store as ISO format string
    else:
        return "TEXT"


class SQLModelMetaclass(type):
    """Metaclass for SQLModel that processes field definitions."""
    
    def __new__(mcs, name: str, bases: tuple, namespace: dict, **kwargs: Any):
        # Get table configuration
        table = kwargs.get("table", False)
        
        # Create the class
        cls = super().__new__(mcs, name, bases, namespace)
        
        # Store table flag
        cls.__table__ = table
        
        # Collect fields from this class and bases
        fields: Dict[str, FieldInfo] = {}
        annotations = {}
        
        # Collect from base classes
        for base in reversed(bases):
            if hasattr(base, "__fields__"):
                fields.update(base.__fields__)
            if hasattr(base, "__annotations__"):
                annotations.update(base.__annotations__)
        
        # Add fields from current class
        if hasattr(cls, "__annotations__"):
            annotations.update(cls.__annotations__)
        
        # Process fields
        for field_name, field_type in annotations.items():
            if field_name.startswith("_"):
                continue
                
            # Get field value from class
            field_value = namespace.get(field_name, ...)
            
            if isinstance(field_value, FieldInfo):
                field_info = field_value
            elif isinstance(field_value, Relationship):
                # Skip relationships for now
                continue
            else:
                # Create default FieldInfo
                if field_value is ...:
                    field_info = FieldInfo(default=None, nullable=True)
                else:
                    field_info = FieldInfo(default=field_value, nullable=True)
            
            # Store field type
            field_info.type = field_type
            field_info.name = field_name
            fields[field_name] = field_info
        
        cls.__fields__ = fields
        cls.__annotations__ = annotations
        
        return cls


class SQLModel(metaclass=SQLModelMetaclass):
    """Base class for SQL models with Pydantic-like behavior."""
    
    __table__: bool = False
    __fields__: Dict[str, FieldInfo] = {}
    __tablename__: Optional[str] = None
    
    def __init__(self, **data: Any):
        # Initialize all fields
        for field_name, field_info in self.__fields__.items():
            if field_name in data:
                value = data[field_name]
            elif field_info.default_factory is not None:
                value = field_info.default_factory()
            elif field_info.default is not None:
                value = field_info.default
            else:
                value = None
            
            setattr(self, field_name, value)
    
    def dict(self, **kwargs: Any) -> Dict[str, Any]:
        """Convert model to dictionary."""
        result = {}
        for field_name in self.__fields__:
            if hasattr(self, field_name):
                value = getattr(self, field_name)
                result[field_name] = value
        return result
    
    def json(self, **kwargs: Any) -> str:
        """Convert model to JSON string."""
        import json
        data = self.dict()
        # Convert datetime objects to ISO format
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return json.dumps(data)
    
    @classmethod
    def get_table_name(cls) -> str:
        """Get the table name for this model."""
        if cls.__tablename__:
            return cls.__tablename__
        return cls.__name__.lower()
    
    @classmethod
    def get_primary_key_field(cls) -> Optional[str]:
        """Get the primary key field name."""
        for field_name, field_info in cls.__fields__.items():
            if field_info.primary_key:
                return field_name
        return None


class Select:
    """Represents a SELECT query."""
    
    def __init__(self, model: Type[SQLModel]):
        self.model = model
        self.where_clauses: List[tuple] = []
    
    def where(self, condition: Any) -> "Select":
        """Add a WHERE clause."""
        self.where_clauses.append(condition)
        return self


def select(model: Type[T]) -> Select:
    """Create a SELECT statement."""
    return Select(model)


class Engine:
    """Database engine wrapper."""
    
    def __init__(self, url: str):
        self.url = url
        # Parse SQLite URL
        if url.startswith("sqlite:///"):
            self.db_path = url[10:]
        else:
            self.db_path = ":memory:"
        self.connection: Optional[sqlite3.Connection] = None
    
    def connect(self) -> sqlite3.Connection:
        """Get or create a connection."""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def close(self):
        """Close the connection."""
        if self.connection:
            self.connection.close()
            self.connection = None


def create_engine(url: str, **kwargs: Any) -> Engine:
    """Create a database engine."""
    return Engine(url)


class Session:
    """Database session for executing queries."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.connection = engine.connect()
        self._objects_to_add: List[SQLModel] = []
    
    def add(self, instance: SQLModel) -> None:
        """Add an instance to the session."""
        self._objects_to_add.append(instance)
    
    def commit(self) -> None:
        """Commit the current transaction."""
        cursor = self.connection.cursor()
        
        for obj in self._objects_to_add:
            table_name = obj.get_table_name()
            fields = obj.__fields__
            
            # Prepare data
            columns = []
            values = []
            placeholders = []
            
            for field_name, field_info in fields.items():
                if hasattr(obj, field_name):
                    value = getattr(obj, field_name)
                    # Skip None values for primary keys on insert
                    if field_info.primary_key and value is None:
                        continue
                    
                    columns.append(field_name)
                    
                    # Convert datetime to string
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    
                    values.append(value)
                    placeholders.append("?")
            
            # Build INSERT query
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(query, values)
            
            # Get the last inserted row id for primary key
            pk_field = obj.get_primary_key_field()
            if pk_field and getattr(obj, pk_field, None) is None:
                setattr(obj, pk_field, cursor.lastrowid)
        
        self.connection.commit()
        self._objects_to_add.clear()
    
    def exec(self, statement: Select) -> "Result":
        """Execute a SELECT statement."""
        model = statement.model
        table_name = model.get_table_name()
        
        # Build query
        query = f"SELECT * FROM {table_name}"
        params = []
        
        # Add WHERE clauses
        if statement.where_clauses:
            where_parts = []
            for condition in statement.where_clauses:
                # Parse condition (simplified)
                if hasattr(condition, "left") and hasattr(condition, "right"):
                    # Binary expression
                    field_name = condition.left.key
                    operator = condition.operator.__name__ if hasattr(condition.operator, "__name__") else "="
                    value = condition.right.value
                    
                    if operator == "eq":
                        where_parts.append(f"{field_name} = ?")
                        params.append(value)
                    elif operator == "gt":
                        where_parts.append(f"{field_name} > ?")
                        params.append(value)
                    elif operator == "lt":
                        where_parts.append(f"{field_name} < ?")
                        params.append(value)
            
            if where_parts:
                query += " WHERE " + " AND ".join(where_parts)
        
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return Result(rows, model)
    
    def refresh(self, instance: SQLModel) -> None:
        """Refresh an instance from the database."""
        model = type(instance)
        table_name = model.get_table_name()
        pk_field = model.get_primary_key_field()
        
        if not pk_field:
            return
        
        pk_value = getattr(instance, pk_field)
        
        cursor = self.connection.cursor()
        query = f"SELECT * FROM {table_name} WHERE {pk_field} = ?"
        cursor.execute(query, (pk_value,))
        row = cursor.fetchone()
        
        if row:
            for key in row.keys():
                if key in model.__fields__:
                    value = row[key]
                    # Convert string back to datetime if needed
                    field_info = model.__fields__[key]
                    if field_info.type is datetime and isinstance(value, str):
                        value = datetime.fromisoformat(value)
                    setattr(instance, key, value)
    
    def close(self) -> None:
        """Close the session."""
        pass


class Result:
    """Query result wrapper."""
    
    def __init__(self, rows: List[sqlite3.Row], model: Type[SQLModel]):
        self.rows = rows
        self.model = model
    
    def all(self) -> List[SQLModel]:
        """Get all results as model instances."""
        results = []
        for row in self.rows:
            data = {}
            for key in row.keys():
                value = row[key]
                # Convert string back to datetime if needed
                if key in self.model.__fields__:
                    field_info = self.model.__fields__[key]
                    if field_info.type is datetime and isinstance(value, str):
                        value = datetime.fromisoformat(value)
                data[key] = value
            results.append(self.model(**data))
        return results
    
    def first(self) -> Optional[SQLModel]:
        """Get the first result."""
        all_results = self.all()
        return all_results[0] if all_results else None
    
    def one(self) -> SQLModel:
        """Get exactly one result, raise if not found or multiple."""
        all_results = self.all()
        if len(all_results) == 0:
            raise Exception("No results found")
        if len(all_results) > 1:
            raise Exception("Multiple results found")
        return all_results[0]


class SQLModelMetadata:
    """Metadata for creating tables."""
    
    def __init__(self):
        self.tables: List[Type[SQLModel]] = []
    
    def create_all(self, engine: Engine) -> None:
        """Create all tables."""
        connection = engine.connect()
        cursor = connection.cursor()
        
        for model in self.tables:
            if not model.__table__:
                continue
            
            table_name = model.get_table_name()
            fields = model.__fields__
            
            # Build CREATE TABLE statement
            columns = []
            for field_name, field_info in fields.items():
                sql_type = _python_type_to_sql(field_info.type)
                column_def = f"{field_name} {sql_type}"
                
                if field_info.primary_key:
                    column_def += " PRIMARY KEY"
                    # Auto-increment for integer primary keys
                    if sql_type == "INTEGER":
                        column_def += " AUTOINCREMENT"
                
                if not field_info.nullable and not field_info.primary_key:
                    column_def += " NOT NULL"
                
                if field_info.unique:
                    column_def += " UNIQUE"
                
                columns.append(column_def)
            
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
            cursor.execute(query)
        
        connection.commit()


# Global metadata instance
metadata = SQLModelMetadata()


def create_all_tables(engine: Engine, models: List[Type[SQLModel]]) -> None:
    """Helper to create all tables for given models."""
    metadata.tables = models
    metadata.create_all(engine)


# Export public API
__all__ = [
    "SQLModel",
    "Field",
    "Relationship",
    "select",
    "Session",
    "Engine",
    "create_engine",
    "create_all_tables",
]