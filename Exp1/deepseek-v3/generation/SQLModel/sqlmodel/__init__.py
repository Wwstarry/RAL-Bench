"""
SQLModel - SQL databases in Python, designed for simplicity, compatibility, and robustness.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Generic
from pydantic import BaseModel, create_model, Field as PydanticField
from pydantic.fields import FieldInfo
import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

# Type variables for generic typing
T = TypeVar('T')
ModelType = TypeVar('ModelType', bound='SQLModel')

class RelationshipInfo:
    """Placeholder for relationship configuration"""
    def __init__(self, **kwargs: Any):
        self._kwargs = kwargs

def Relationship(**kwargs: Any) -> Any:
    """Create relationship configuration"""
    return RelationshipInfo(**kwargs)

class Field(PydanticField):
    """Extended Field that works with both Pydantic and SQLAlchemy-like operations"""
    
    def __init__(
        self,
        default: Any = ...,
        *,
        default_factory: Any = None,
        alias: str = None,
        title: str = None,
        description: str = None,
        gt: float = None,
        ge: float = None,
        lt: float = None,
        le: float = None,
        min_length: int = None,
        max_length: int = None,
        regex: str = None,
        primary_key: bool = False,
        foreign_key: Any = None,
        nullable: bool = True,
        index: bool = False,
        sa_column: Any = None,
        **extra: Any,
    ):
        super().__init__(
            default=default,
            default_factory=default_factory,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
            **extra,
        )
        self.primary_key = primary_key
        self.foreign_key = foreign_key
        self.nullable = nullable
        self.index = index
        self.sa_column = sa_column

class MetaModel(type):
    """Metaclass that handles both Pydantic and table metadata"""
    
    def __new__(cls, name: str, bases: tuple, namespace: dict):
        # Extract table configuration
        table_name = namespace.get('__tablename__')
        metadata = namespace.get('metadata', {})
        
        # Create the class
        new_class = super().__new__(cls, name, bases, namespace)
        
        # Store table metadata
        if table_name:
            new_class.__table__ = TableMetadata(table_name, new_class, metadata)
        
        return new_class

class TableMetadata:
    """Simple table metadata storage"""
    
    def __init__(self, name: str, model_class: Type, metadata: Dict[str, Any]):
        self.name = name
        self.model_class = model_class
        self.columns = {}
        self.primary_key = None
        
        # Extract column information from model fields
        for field_name, field_info in model_class.model_fields.items():
            if hasattr(field_info, 'primary_key') and field_info.primary_key:
                self.primary_key = field_name
            self.columns[field_name] = field_info

class SQLModel(BaseModel, metaclass=MetaModel):
    """Base class for SQLModel models"""
    
    # Table configuration
    __tablename__: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **data: Any):
        super().__init__(**data)
    
    @classmethod
    def model_validate(cls: Type[ModelType], obj: Any) -> ModelType:
        """Validate data against the model"""
        if isinstance(obj, dict):
            return cls(**obj)
        return cls(**obj.dict() if hasattr(obj, 'dict') else dict(obj))
    
    def model_dump(self, *args, **kwargs) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return super().model_dump(*args, **kwargs)
    
    def model_dump_json(self, *args, **kwargs) -> str:
        """Convert model to JSON string"""
        return super().model_dump_json(*args, **kwargs)
    
    @classmethod
    def from_orm(cls: Type[ModelType], obj: Any) -> ModelType:
        """Create model instance from ORM object"""
        return cls.model_validate(obj)
    
    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """Alias for model_dump for compatibility"""
        return self.model_dump(*args, **kwargs)
    
    def json(self, *args, **kwargs) -> str:
        """Alias for model_dump_json for compatibility"""
        return self.model_dump_json(*args, **kwargs)

class Session:
    """Simple session implementation for database operations"""
    
    def __init__(self, engine=None):
        self.engine = engine
        self._objects = []
        self._updated_objects = []
        self._deleted_objects = []
    
    def add(self, instance: SQLModel) -> None:
        """Add an instance to the session"""
        if instance not in self._objects:
            self._objects.append(instance)
    
    def add_all(self, instances: List[SQLModel]) -> None:
        """Add multiple instances to the session"""
        for instance in instances:
            self.add(instance)
    
    def commit(self) -> None:
        """Commit changes - in this pure Python version, just mark as committed"""
        self._updated_objects.extend(self._objects)
        self._objects.clear()
        self._deleted_objects.clear()
    
    def refresh(self, instance: SQLModel) -> None:
        """Refresh instance data - no-op in pure Python version"""
        pass
    
    def query(self, model: Type[SQLModel]) -> 'Query':
        """Create a query for the specified model"""
        return Query(model, self._updated_objects)
    
    def exec(self, statement) -> 'Query':
        """Execute a select statement"""
        if hasattr(statement, 'model'):
            return Query(statement.model, self._updated_objects)
        return Query(None, self._updated_objects)
    
    def close(self) -> None:
        """Close the session"""
        self._objects.clear()
        self._updated_objects.clear()
        self._deleted_objects.clear()

class Query:
    """Simple query implementation for filtering results"""
    
    def __init__(self, model: Type[SQLModel], objects: List[SQLModel]):
        self.model = model
        self._objects = [obj for obj in objects if isinstance(obj, model)] if model else objects
        self._filters = []
    
    def filter(self, *args, **kwargs) -> 'Query':
        """Add filter conditions"""
        self._filters.append((args, kwargs))
        return self
    
    def where(self, *args, **kwargs) -> 'Query':
        """Alias for filter"""
        return self.filter(*args, **kwargs)
    
    def all(self) -> List[SQLModel]:
        """Get all results after applying filters"""
        results = self._objects
        
        for filter_args, filter_kwargs in self._filters:
            # Simple attribute-based filtering
            for obj in results[:]:
                match = True
                
                # Handle keyword filters
                for key, value in filter_kwargs.items():
                    if hasattr(obj, key):
                        attr_value = getattr(obj, key)
                        if callable(value):
                            if not value(attr_value):
                                match = False
                                break
                        elif attr_value != value:
                            match = False
                            break
                
                if not match:
                    results.remove(obj)
        
        return results
    
    def first(self) -> Optional[SQLModel]:
        """Get first result after applying filters"""
        results = self.all()
        return results[0] if results else None
    
    def one(self) -> SQLModel:
        """Get exactly one result, raise error if not exactly one"""
        results = self.all()
        if len(results) != 1:
            raise ValueError("Expected exactly one result")
        return results[0]
    
    def count(self) -> int:
        """Count results after applying filters"""
        return len(self.all())

def select(model: Type[SQLModel]) -> 'Select':
    """Create a select statement"""
    return Select(model)

class Select:
    """Simple select statement implementation"""
    
    def __init__(self, model: Type[SQLModel]):
        self.model = model
    
    def where(self, *args, **kwargs) -> 'Select':
        """Add where conditions - in this simple implementation, just return self"""
        return self
    
    def filter(self, *args, **kwargs) -> 'Select':
        """Add filter conditions - alias for where"""
        return self.where(*args, **kwargs)

class Engine:
    """Simple engine implementation"""
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string
    
    def connect(self) -> 'Connection':
        """Create a connection"""
        return Connection(self)
    
    def dispose(self) -> None:
        """Clean up resources"""
        pass

class Connection:
    """Simple connection implementation"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def close(self) -> None:
        """Close the connection"""
        pass

def create_engine(connection_string: str) -> Engine:
    """Create a database engine"""
    return Engine(connection_string)

# Utility functions for compatibility
def create_all(engine: Engine) -> None:
    """Create all tables - no-op in pure Python version"""
    pass

def drop_all(engine: Engine) -> None:
    """Drop all tables - no-op in pure Python version"""
    pass

# Export the public API
__all__ = [
    'SQLModel',
    'Field',
    'Relationship',
    'Session',
    'select',
    'create_engine',
    'create_all',
    'drop_all',
    'Engine',
]

# Version info
__version__ = "0.0.1"