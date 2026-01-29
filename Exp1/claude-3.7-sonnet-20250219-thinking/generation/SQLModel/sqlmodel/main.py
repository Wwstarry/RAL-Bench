from typing import Any, Dict, List, Optional, Type, TypeVar, Union, get_type_hints, ClassVar, Callable, Set
import inspect
from datetime import datetime
import json
from pydantic import BaseModel, create_model, validator
from pydantic.fields import ModelField
from pydantic.main import ModelMetaclass

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import relationship as sa_relationship, mapped_column
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.sql.schema import MetaData

SQLModelMetaData = MetaData()
BaseClass = declarative_base(metadata=SQLModelMetaData)

T = TypeVar("T")


class FieldInfo:
    def __init__(
        self, 
        default: Any = ..., 
        default_factory: Optional[Callable[[], Any]] = None,
        primary_key: bool = False,
        foreign_key: Optional[str] = None,
        nullable: bool = True,
        index: bool = False,
        unique: bool = False,
        sa_type=None,
        sa_column: Optional[Column] = None,
        sa_column_args: List[Any] = None,
        sa_column_kwargs: Dict[str, Any] = None,
        **extra: Any
    ):
        self.default = default
        self.default_factory = default_factory
        self.primary_key = primary_key
        self.foreign_key = foreign_key
        self.nullable = nullable
        self.index = index
        self.unique = unique
        self.sa_type = sa_type
        self.sa_column = sa_column
        self.sa_column_args = sa_column_args or []
        self.sa_column_kwargs = sa_column_kwargs or {}
        self.extra = extra


class Field:
    def __new__(
        cls,
        default: Any = ...,
        *,
        default_factory: Optional[Callable[[], Any]] = None,
        primary_key: bool = False,
        foreign_key: Optional[str] = None,
        nullable: bool = True,
        index: bool = False,
        unique: bool = False,
        sa_type=None,
        sa_column: Optional[Column] = None,
        **extra: Any
    ) -> Any:
        field_info = FieldInfo(
            default=default,
            default_factory=default_factory,
            primary_key=primary_key,
            foreign_key=foreign_key,
            nullable=nullable,
            index=index,
            unique=unique,
            sa_type=sa_type,
            sa_column=sa_column,
            **extra
        )
        if default is not ...:
            return field_info, default
        return field_info


class RelationshipInfo:
    def __init__(self, related_model: str, back_populates: Optional[str] = None, **kwargs):
        self.related_model = related_model
        self.back_populates = back_populates
        self.kwargs = kwargs


class Relationship:
    def __new__(cls, related_model: str, *, back_populates: Optional[str] = None, **kwargs):
        return RelationshipInfo(related_model=related_model, back_populates=back_populates, **kwargs)


class SQLModelMetaclass(ModelMetaclass, DeclarativeMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        # Get tablename from kwargs or generate from class name
        tablename = kwargs.pop("tablename", namespace.pop("__tablename__", name.lower()))
        
        # Process annotations for SQLAlchemy columns
        annotations = namespace.get("__annotations__", {})
        for field_name, field_type in annotations.items():
            if field_name in namespace:
                value = namespace[field_name]
                if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], FieldInfo):
                    field_info, default = value
                    namespace[field_name] = default
                    
                    # Create SQLAlchemy column
                    if not field_info.sa_column:
                        column_args = field_info.sa_column_args
                        if field_info.foreign_key:
                            column_args.append(ForeignKey(field_info.foreign_key))
                        
                        column_kwargs = {
                            "primary_key": field_info.primary_key,
                            "nullable": field_info.nullable and not field_info.primary_key,
                            "index": field_info.index,
                            "unique": field_info.unique,
                            **field_info.sa_column_kwargs
                        }
                        
                        # Determine column type from Python type annotation
                        sa_type = field_info.sa_type
                        if not sa_type:
                            if field_type == int or field_type == Optional[int]:
                                sa_type = Integer
                            elif field_type == str or field_type == Optional[str]:
                                sa_type = String(length=255)
                            elif field_type == bool or field_type == Optional[bool]:
                                sa_type = Boolean
                            elif field_type == float or field_type == Optional[float]:
                                sa_type = Float
                            elif field_type == datetime or field_type == Optional[datetime]:
                                sa_type = DateTime
                        
                        column = Column(field_name, sa_type, *column_args, **column_kwargs)
                        namespace[f"_{field_name}_sa_column"] = column
                elif isinstance(value, RelationshipInfo):
                    relationship_info = value
                    namespace[field_name] = sa_relationship(
                        relationship_info.related_model,
                        back_populates=relationship_info.back_populates,
                        **relationship_info.kwargs
                    )
        
        # Set __tablename__ for SQLAlchemy
        namespace["__tablename__"] = tablename
        
        # Create the class with both Pydantic and SQLAlchemy
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        return cls


class SQLModel(BaseModel, BaseClass, metaclass=SQLModelMetaclass):
    __abstract__ = True
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
        
    def dict(self, *args, **kwargs):
        exclude = kwargs.get("exclude", set())
        # Filter out SQLAlchemy private attributes
        return super().dict(
            *args, 
            **{
                **kwargs,
                "exclude": {
                    *exclude, 
                    *{
                        k for k in self.__dict__ 
                        if k.startswith('_sa_') or k.startswith('_') and k.endswith('_sa_column')
                    }
                }
            }
        )
    
    def json(self, *args, **kwargs):
        return json.dumps(self.dict(*args, **kwargs))