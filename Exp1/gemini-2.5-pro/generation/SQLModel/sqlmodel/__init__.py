# This is a pure Python, in-memory implementation of the core SQLModel API.
# It is designed to be a drop-in replacement for black-box testing purposes,
# mimicking the behavior of SQLModel without requiring a real database or SQLAlchemy.

import json
from typing import Any, Dict, List, Optional, Type, Union, Iterable, TypeVar, ClassVar

try:
    import pydantic
    from pydantic import BaseModel
    from pydantic.fields import FieldInfo, Undefined
    from pydantic.main import ModelMetaclass as PydanticModelMetaclass
except ImportError:
    raise ImportError("pydantic is required to use this mock sqlmodel. Please `pip install pydantic`.")


# --- In-memory Database ---
# This global dictionary simulates a database.
# create_engine() will reset it to ensure test isolation.
_db_storage: Dict[str, Any] = {
    "tables": {},  # Stores schema: {"table_name": {"pk_name": "id", ...}}
    "data": {},    # Stores data: {"table_name": {pk_val: {col: val, ...}}}
    "sequences": {} # Stores auto-increment counters: {"table_name": last_id}
}


# --- Core Components ---

class SQLModelError(Exception):
    """Base exception for this library."""
    pass

class NoResultFound(SQLModelError):
    """Raised by .one() when no result is found."""
    pass

class MultipleResultsFound(SQLModelError):
    """Raised by .one() when multiple results are found."""
    pass


# --- Query Building ---

class BinaryExpression:
    """Represents a binary expression in a WHERE clause, e.g., `Hero.name == "Spidey"`."""
    def __init__(self, left: 'QueryableAttribute', op: str, right: Any):
        self.left = left
        self.op = op
        self.right = right

class QueryableAttribute:
    """A descriptor that allows class attributes to be used in queries."""
    def __init__(self, name: str):
        self.name = name

    def __get__(self, instance: Optional['SQLModel'], owner: Type['SQLModel']) -> Any:
        if instance is None:
            # Class access, e.g., `Hero.name` in `select(Hero).where(Hero.name == ...)`
            return self
        # Instance access, e.g., `my_hero.name`
        return instance.__dict__.get(self.name)

    def __eq__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, "==", other)

    def __ne__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, "!=", other)


# --- Select Statement ---

T = TypeVar("T", bound="SQLModel")

class Select:
    """Represents a SELECT statement."""
    def __init__(self, entity: Type[T]):
        if not issubclass(entity, SQLModel):
            raise TypeError(f"{entity.__name__} is not a SQLModel model.")
        self.entity = entity
        self._where_clauses: List[BinaryExpression] = []

    def where(self, *clauses: BinaryExpression) -> 'Select':
        """Adds WHERE clauses to the select statement."""
        for clause in clauses:
            if not isinstance(clause, BinaryExpression):
                raise TypeError("where() argument must be a binary expression, e.g., `Model.field == value`")
            self._where_clauses.append(clause)
        return self

def select(*entities: Type[T]) -> Select[T]:
    """Creates a SELECT statement."""
    if len(entities) != 1:
        raise NotImplementedError("This mock only supports select from a single model.")
    return Select(entities[0])


# --- Result Handling ---

class Result:
    """Holds the results of a query execution."""
    def __init__(self, results: List[T]):
        self._results = results

    def all(self) -> List[T]:
        """Return all results in a list."""
        return self._results

    def one(self) -> T:
        """Return exactly one result or raise an error."""
        if len(self._results) == 0:
            raise NoResultFound("No row was found for one()")
        if len(self._results) > 1:
            raise MultipleResultsFound("Multiple rows were found for one()")
        return self._results[0]

    def first(self) -> Optional[T]:
        """Return the first result or None if no results."""
        return self._results[0] if self._results else None

    def __iter__(self) -> Iterable[T]:
        """Allows iterating over the results."""
        return iter(self._results)


# --- Metadata and Model Definition ---

class MetaData:
    """A container for schema information."""
    def __init__(self):
        self.models: List[Type['SQLModel']] = []

    def create_all(self, bind: 'Engine'):
        """Creates all tables in the in-memory database."""
        storage = bind._storage
        for model in self.models:
            meta = model.__sqlmodel_meta__
            table_name = meta["table_name"]
            storage["tables"][table_name] = meta
            storage["data"][table_name] = {}
            # Initialize sequence for auto-incrementing integer PKs
            if meta.get("pk_is_int"):
                storage["sequences"][table_name] = 0

class SQLModelMetaclass(PydanticModelMetaclass):
    """Metaclass to capture schema information from model definitions."""
    def __new__(mcs, name: str, bases: tuple, dct: dict, **kwargs: Any):
        cls = super().__new__(mcs, name, bases, dct, **kwargs)

        is_base_model = any(b.__name__ == 'SQLModel' and b.__module__ == __name__ for b in bases)
        if not is_base_model and name == 'SQLModel': # Is the SQLModel class itself
            cls.metadata = MetaData()
            return cls
        
        # Don't process Pydantic's own base models or our base
        if not is_base_model:
            return cls

        if not hasattr(cls, 'metadata'):
            cls.metadata = SQLModel.metadata

        meta: Dict[str, Any] = {
            "table_name": name.lower(),
            "columns": {},
            "pk_name": None,
            "pk_is_int": False,
        }
        pk_found = False

        for field_name, field_info in cls.model_fields.items():
            meta["columns"][field_name] = field_info
            is_pk = (
                hasattr(field_info, 'json_schema_extra') and
                isinstance(field_info.json_schema_extra, dict) and
                field_info.json_schema_extra.get("primary_key") is True
            )

            if is_pk:
                if pk_found:
                    raise TypeError(f"Model '{name}' has multiple primary keys. Only one is allowed.")
                pk_found = True
                meta["pk_name"] = field_name
                
                field_type = cls.__annotations__.get(field_name)
                origin = getattr(field_type, '__origin__', None)
                args = getattr(field_type, '__args__', ())
                if field_type is int or (origin in (Union, Optional) and int in args):
                    meta["pk_is_int"] = True

        cls.__sqlmodel_meta__ = meta
        
        if cls not in cls.metadata.models:
            cls.metadata.models.append(cls)

        for field_name in cls.model_fields:
            setattr(cls, field_name, QueryableAttribute(field_name))

        return cls

class SQLModel(BaseModel, metaclass=SQLModelMetaclass):
    """Base class for all SQLModel models."""
    metadata: ClassVar[MetaData]
    __sqlmodel_meta__: ClassVar[Dict[str, Any]]

    model_config = pydantic.ConfigDict(from_attributes=True)

    def __init__(self, **data: Any):
        super().__init__(**data)

    def dict(self, **kwargs: Any) -> Dict[str, Any]:
        return self.model_dump(**kwargs)

    def json(self, **kwargs: Any) -> str:
        return self.model_dump_json(**kwargs)

def Field(default: Any = Undefined, *, primary_key: bool = False, **kwargs: Any) -> Any:
    """A wrapper around Pydantic's Field that adds SQL-specific parameters."""
    json_schema_extra = kwargs.pop("json_schema_extra", {}) or {}
    if primary_key:
        json_schema_extra["primary_key"] = True
    
    return pydantic.Field(default=default, json_schema_extra=json_schema_extra, **kwargs)

def Relationship(*, back_populates: Optional[str] = None) -> Any:
    """A dummy implementation of Relationship for API compatibility."""
    return Field(default=None, exclude=True)


# --- Engine and Session ---

class Engine:
    """Represents the connection to the in-memory database."""
    def __init__(self, url: str, echo: bool = False):
        self.url = url
        self.echo = echo
        self._storage = _db_storage

    def connect(self) -> 'Engine':
        return self

    def __enter__(self) -> 'Engine':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

def create_engine(url: str, **kwargs: Any) -> Engine:
    """Creates an engine and resets the in-memory database for test isolation."""
    _db_storage["tables"].clear()
    _db_storage["data"].clear()
    _db_storage["sequences"].clear()
    if hasattr(SQLModel, 'metadata') and isinstance(SQLModel.metadata, MetaData):
        SQLModel.metadata.models.clear()
        
    return Engine(url, **kwargs)

class Session:
    """Manages persistence operations for model instances."""
    def __init__(self, engine: Engine):
        if not isinstance(engine, Engine):
            raise TypeError(f"Session requires an Engine instance, not {type(engine)}")
        self._engine = engine
        self._storage = engine._storage
        self._new: List[SQLModel] = []

    def __enter__(self) -> 'Session':
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def add(self, instance: SQLModel) -> None:
        """Stage an instance to be inserted into the database."""
        if not isinstance(instance, SQLModel):
            raise TypeError("Can only add SQLModel instances to the session.")
        if instance not in self._new:
            self._new.append(instance)

    def commit(self) -> None:
        """Persist all staged changes to the in-memory database."""
        for instance in self._new:
            meta = instance.__sqlmodel_meta__
            table_name = meta["table_name"]
            pk_name = meta["pk_name"]

            if pk_name is None:
                raise TypeError(f"Model '{type(instance).__name__}' has no primary key and cannot be committed.")

            pk_val = getattr(instance, pk_name)

            if pk_val is None and meta["pk_is_int"]:
                self._storage["sequences"][table_name] += 1
                pk_val = self._storage["sequences"][table_name]
                object.__setattr__(instance, pk_name, pk_val)

            if pk_val is None:
                raise SQLModelError(f"Primary key '{pk_name}' cannot be None on commit for instance: {instance}")

            self._storage["data"][table_name][pk_val] = instance.model_dump()
        
        self._new.clear()

    def exec(self, statement: Select[T]) -> Result[T]:
        """Execute a statement (only SELECT is supported)."""
        if not isinstance(statement, Select):
            raise NotImplementedError("This mock only supports `select` statements in `exec`.")

        model = statement.entity
        meta = model.__sqlmodel_meta__
        table_name = meta["table_name"]

        if table_name not in self._storage["data"]:
            raise SQLModelError(f"Table '{table_name}' not found. Did you run `SQLModel.metadata.create_all(engine)`?")

        all_rows = list(self._storage["data"][table_name].values())
        
        def check_match(row_dict: Dict[str, Any], clause: BinaryExpression) -> bool:
            col_name = clause.left.name
            op = clause.op
            value = clause.right
            row_value = row_dict.get(col_name)

            if op == "==": return row_value == value
            if op == "!=": return row_value != value
            raise NotImplementedError(f"Operator '{op}' is not implemented.")

        if not statement._where_clauses:
            filtered_rows = all_rows
        else:
            filtered_rows = [
                row_dict for row_dict in all_rows 
                if all(check_match(row_dict, clause) for clause in statement._where_clauses)
            ]

        results = [model.model_validate(row) for row in filtered_rows]
        return Result(results)

    def refresh(self, instance: SQLModel) -> None:
        """Update an instance with the data from the in-memory database."""
        meta = instance.__sqlmodel_meta__
        table_name = meta["table_name"]
        pk_name = meta["pk_name"]

        if pk_name is None:
            raise ValueError("Cannot refresh an instance of a model with no primary key.")
            
        pk_val = getattr(instance, pk_name)
        if pk_val is None:
            raise ValueError("Cannot refresh instance with a non-set primary key.")

        stored_data = self._storage["data"][table_name].get(pk_val)
        if stored_data is None:
            raise SQLModelError(f"Instance with pk {pk_val} not found in the database for refresh.")

        for key, value in stored_data.items():
            object.__setattr__(instance, key, value)

    def get(self, entity: Type[T], ident: Any) -> Optional[T]:
        """Retrieve an instance by its primary key."""
        meta = entity.__sqlmodel_meta__
        table_name = meta["table_name"]
        
        if table_name not in self._storage["data"]:
            return None
            
        row_dict = self._storage["data"][table_name].get(ident)
        if row_dict:
            return entity.model_validate(row_dict)
        return None

    def close(self) -> None:
        """Close the session. (No-op in this mock)."""
        self._new.clear()