import typing
from typing import Any, Dict, Optional, Type, TypeVar, Union, List, Tuple

import pydantic
from pydantic import BaseModel
from pydantic.fields import FieldInfo

import sqlalchemy
from sqlalchemy import Column, ForeignKey, inspect
from sqlalchemy import create_engine as _create_engine
from sqlalchemy.orm import (
    registry,
    relationship as _relationship,
    Session as _Session,
    declared_attr,
    InstrumentedAttribute
)
from sqlalchemy.sql.expression import Select
from sqlalchemy.future import select as _select

# -----------------------------------------------------------------------------
# Globals and Registry
# -----------------------------------------------------------------------------

_sa_registry = registry()
metadata = _sa_registry.metadata

# -----------------------------------------------------------------------------
# Field Definition
# -----------------------------------------------------------------------------

class SQLModelFieldInfo(FieldInfo):
    def __init__(self, default: Any = ..., **kwargs: Any) -> None:
        self.primary_key = kwargs.pop("primary_key", False)
        self.nullable = kwargs.pop("nullable", None)
        self.foreign_key = kwargs.pop("foreign_key", None)
        self.index = kwargs.pop("index", False)
        self.sa_column = kwargs.pop("sa_column", None)
        self.sa_column_args = kwargs.pop("sa_column_args", None)
        self.sa_column_kwargs = kwargs.pop("sa_column_kwargs", None)
        super().__init__(default=default, **kwargs)

def Field(
    default: Any = ...,
    *,
    primary_key: bool = False,
    nullable: Union[bool, None] = None,
    foreign_key: Optional[str] = None,
    index: bool = False,
    sa_column: Union[Column, None] = None,
    sa_column_args: Union[List[Any], None] = None,
    sa_column_kwargs: Union[Dict[str, Any], None] = None,
    **kwargs: Any,
) -> Any:
    return SQLModelFieldInfo(
        default,
        primary_key=primary_key,
        nullable=nullable,
        foreign_key=foreign_key,
        index=index,
        sa_column=sa_column,
        sa_column_args=sa_column_args,
        sa_column_kwargs=sa_column_kwargs,
        **kwargs,
    )

def Relationship(
    *,
    back_populates: Optional[str] = None,
    link_model: Optional[Any] = None,
    sa_relationship: Optional[Any] = None,
    sa_relationship_args: Optional[List[Any]] = None,
    sa_relationship_kwargs: Optional[Dict[str, Any]] = None,
) -> Any:
    # In a full implementation, this would handle link models (many-to-many).
    # For basic compatibility, we wrap sqlalchemy.orm.relationship.
    kwargs = {}
    if back_populates:
        kwargs["back_populates"] = back_populates
    if sa_relationship_kwargs:
        kwargs.update(sa_relationship_kwargs)
    
    return _relationship(**kwargs)

# -----------------------------------------------------------------------------
# Metaclass and Model
# -----------------------------------------------------------------------------

def _get_sqlalchemy_type(python_type: Type) -> Any:
    """Map Python types to SQLAlchemy types."""
    if python_type is int:
        return sqlalchemy.Integer
    if python_type is str:
        return sqlalchemy.String
    if python_type is bool:
        return sqlalchemy.Boolean
    if python_type is float:
        return sqlalchemy.Float
    # Handle Optional[T]
    if typing.get_origin(python_type) is Union:
        args = typing.get_args(python_type)
        if type(None) in args:
            # Find the non-None type
            for arg in args:
                if arg is not type(None):
                    return _get_sqlalchemy_type(arg)
    return sqlalchemy.String # Default fallback

class SQLModelMetaclass(type(BaseModel)):
    def __new__(cls, name, bases, class_dict, **kwargs):
        table = kwargs.pop("table", False)
        registry = kwargs.pop("registry", _sa_registry)
        
        # Create the Pydantic class
        new_cls = super().__new__(cls, name, bases, class_dict, **kwargs)
        
        if table:
            # 1. Determine Table Name
            tablename = class_dict.get("__tablename__")
            if not tablename:
                tablename = name.lower()
                setattr(new_cls, "__tablename__", tablename)

            # 2. Construct SQLAlchemy Columns from Pydantic Fields
            # Support Pydantic V1 and V2 field access
            fields = getattr(new_cls, "model_fields", None)
            if fields is None:
                fields = getattr(new_cls, "__fields__", {})

            cols = []
            
            for field_name, field_value in fields.items():
                # Handle Pydantic V1 vs V2 FieldInfo structure
                field_info = getattr(field_value, "field_info", field_value)
                
                # Check if it's a Relationship (skip columns)
                # In a real implementation, we'd detect RelationshipInfo. 
                # Here we assume if it's not a SQLModelFieldInfo or standard type, check annotations.
                
                # Determine SQL Type
                type_annotation = field_value.annotation if hasattr(field_value, "annotation") else field_value.type_
                sa_type = _get_sqlalchemy_type(type_annotation)

                # Extract metadata
                is_pk = getattr(field_info, "primary_key", False)
                is_fk = getattr(field_info, "foreign_key", None)
                is_idx = getattr(field_info, "index", False)
                is_nullable = getattr(field_info, "nullable", None)
                
                # If nullable is not explicitly set, infer from Optional type
                if is_nullable is None:
                    origin = typing.get_origin(type_annotation)
                    if origin is Union and type(None) in typing.get_args(type_annotation):
                        is_nullable = True
                    else:
                        is_nullable = False

                # If primary key, nullable must be False (usually)
                if is_pk:
                    is_nullable = False

                col_args = []
                col_kwargs = {
                    "primary_key": is_pk,
                    "nullable": is_nullable,
                    "index": is_idx
                }

                if is_fk:
                    col_args.append(ForeignKey(is_fk))

                # Create Column
                # If sa_column is provided directly in Field(), use it
                custom_sa_col = getattr(field_info, "sa_column", None)
                
                if custom_sa_col is not None:
                    # If a column object is passed, we must clone it or use it, 
                    # but usually we map it to the attribute name.
                    # For imperative mapping, we define the table separately.
                    col = custom_sa_col
                    col.name = field_name
                else:
                    col = Column(field_name, sa_type, *col_args, **col_kwargs)
                
                cols.append(col)

            # 3. Create the SQLAlchemy Table
            # We use the global metadata
            table_obj = sqlalchemy.Table(tablename, metadata, *cols, extend_existing=True)
            
            # 4. Map the class imperatively
            # This binds the Pydantic class to the SQLAlchemy Table
            registry.map_imperatively(new_cls, table_obj)

        return new_cls

class SQLModel(BaseModel, metaclass=SQLModelMetaclass):
    # Configuration for Pydantic to allow arbitrary types (needed for SQLAlchemy internals)
    model_config = {"arbitrary_types_allowed": True}
    
    # Pydantic V1 compatibility
    class Config:
        arbitrary_types_allowed = True

    metadata = metadata

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

# -----------------------------------------------------------------------------
# Session and Engine
# -----------------------------------------------------------------------------

def create_engine(*args, **kwargs):
    return _create_engine(*args, **kwargs)

class Session(_Session):
    def exec(self, statement: Union[Select, str]) -> Any:
        results = self.execute(statement)
        return results.scalars()

    def get(self, entity, ident):
        return super().get(entity, ident)

# -----------------------------------------------------------------------------
# Query Utilities
# -----------------------------------------------------------------------------

def select(*entities) -> Select:
    return _select(*entities)

def col(field) -> Any:
    """
    Helper to get the SQLAlchemy column from a SQLModel field if needed.
    In most cases, the class attribute itself acts as the column expression.
    """
    return field