"""
A small, pure-Python subset of SQLModel built on top of Pydantic + SQLAlchemy.

Goal: be API-compatible with the core parts of SQLModel used by the tests:
- SQLModel base class for Pydantic models + SQLAlchemy ORM mapping
- Field helper for defaults/metadata
- select() helper (SQLAlchemy select)
- Relationship helper
- Session and engine utilities (create_engine, Session)
"""

from __future__ import annotations

import inspect
from typing import Any, Dict, Optional, Type, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic import Field as PydanticField

from sqlalchemy import Column, Integer
from sqlalchemy.orm import DeclarativeMeta, registry, relationship as sa_relationship, sessionmaker
from sqlalchemy.orm import Session as _SASession
from sqlalchemy import create_engine as _sa_create_engine
from sqlalchemy.sql import select as _sa_select


__all__ = [
    "SQLModel",
    "Field",
    "select",
    "Relationship",
    "Session",
    "create_engine",
]


# --- Public helpers ---

def Field(
    default: Any = inspect._empty,
    *,
    default_factory: Any = None,
    primary_key: bool = False,
    nullable: Optional[bool] = None,
    index: Optional[bool] = None,
    unique: Optional[bool] = None,
    foreign_key: Optional[str] = None,
    sa_column: Any = None,
    **kwargs: Any,
) -> Any:
    """
    Pydantic-compatible Field with a few SQLModel-ish extra kwargs.
    We stash SQL-related info onto FieldInfo.extra for model building.
    """
    extra = dict(kwargs.pop("extra", {}) or {})
    extra.update(
        {
            "primary_key": primary_key,
            "nullable": nullable,
            "index": index,
            "unique": unique,
            "foreign_key": foreign_key,
            "sa_column": sa_column,
        }
    )

    if default is inspect._empty:
        return PydanticField(default_factory=default_factory, **kwargs, extra=extra)
    return PydanticField(default, default_factory=default_factory, **kwargs, extra=extra)


def Relationship(*, back_populates: Optional[str] = None, sa_relationship_kwargs: Optional[dict] = None, **kwargs: Any):
    """
    Lightweight proxy to sqlalchemy.orm.relationship.
    """
    rel_kwargs = {}
    if back_populates is not None:
        rel_kwargs["back_populates"] = back_populates
    if sa_relationship_kwargs:
        rel_kwargs.update(sa_relationship_kwargs)
    rel_kwargs.update(kwargs)
    return ("__sqlmodel_relationship__", rel_kwargs)


def select(*entities: Any) -> Any:
    return _sa_select(*entities)


def create_engine(*args: Any, **kwargs: Any):
    return _sa_create_engine(*args, **kwargs)


class Session(_SASession):
    """
    SQLModel exports sqlalchemy.orm.Session directly. We subclass for safety and
    to allow future compatibility shims.
    """
    pass


# --- Internals: mapping Pydantic to SQLAlchemy ---

_mapper_registry = registry()
_T = TypeVar("_T")


def _is_optional(tp: Any) -> bool:
    origin = get_origin(tp)
    if origin is Union:
        args = get_args(tp)
        return any(a is type(None) for a in args)
    return False


def _optional_inner(tp: Any) -> Any:
    origin = get_origin(tp)
    if origin is Union:
        args = tuple(a for a in get_args(tp) if a is not type(None))
        if len(args) == 1:
            return args[0]
    return tp


def _python_type_to_sa_column_type(py_type: Any):
    # Minimal set needed by tests; SQLAlchemy can infer many via python_type,
    # but we map common ones explicitly.
    from sqlalchemy import Boolean, Date, DateTime, Float, LargeBinary, String, Text
    from sqlalchemy import JSON as SAJSON
    from sqlalchemy import Numeric
    import datetime
    import decimal
    import uuid

    t = py_type
    if t is int:
        return Integer
    if t is float:
        return Float
    if t is bool:
        return Boolean
    if t is str:
        return String
    if t is bytes:
        return LargeBinary
    if t is datetime.date:
        return Date
    if t is datetime.datetime:
        return DateTime
    if t is decimal.Decimal:
        return Numeric
    if t is dict or t is list:
        return SAJSON
    if t is uuid.UUID:
        # Store UUIDs as string by default for portability.
        return String(36)
    # Fallback to String; good enough for many tests that don't assert type.
    return Text


def _build_columns_for_model(cls: Type[Any]) -> Dict[str, Column]:
    cols: Dict[str, Column] = {}
    annotations = getattr(cls, "__annotations__", {}) or {}
    pyd_fields = getattr(cls, "__fields__", {}) or {}

    for name, ann in annotations.items():
        if name.startswith("_"):
            continue

        # Relationship marker?
        rel_marker = getattr(cls, name, None)
        if isinstance(rel_marker, tuple) and len(rel_marker) == 2 and rel_marker[0] == "__sqlmodel_relationship__":
            continue

        # If already set to a SQLAlchemy Column, keep it.
        current = getattr(cls, name, None)
        if isinstance(current, Column):
            cols[name] = current
            continue

        fi: Optional[FieldInfo] = None
        if name in pyd_fields:
            fi = pyd_fields[name].field_info

        extra = (fi.extra if fi is not None else {}) or {}
        sa_column = extra.get("sa_column")
        if sa_column is not None:
            if isinstance(sa_column, Column):
                cols[name] = sa_column
                continue

        primary_key = bool(extra.get("primary_key", False))
        nullable = extra.get("nullable", None)
        index = extra.get("index", None)
        unique = extra.get("unique", None)
        foreign_key = extra.get("foreign_key", None)

        tp = _optional_inner(ann)
        col_type = _python_type_to_sa_column_type(tp)

        # Default / server_default behavior: keep simple; use python-side default.
        default = None
        has_default = False
        if fi is not None:
            if fi.default is not None and fi.default is not inspect._empty:
                default = fi.default
                has_default = True
            elif fi.default_factory is not None:
                # SQLAlchemy default can be callable; keep it.
                default = fi.default_factory
                has_default = True

        # Determine nullability:
        # - explicit nullable wins
        # - primary keys are not nullable
        # - Optional[...] implies nullable
        if nullable is None:
            if primary_key:
                nullable_val = False
            else:
                nullable_val = _is_optional(ann)
        else:
            nullable_val = bool(nullable)

        col_kwargs: Dict[str, Any] = {"primary_key": primary_key, "nullable": nullable_val}
        if index is not None:
            col_kwargs["index"] = bool(index)
        if unique is not None:
            col_kwargs["unique"] = bool(unique)
        if foreign_key is not None:
            from sqlalchemy import ForeignKey

            col_kwargs["foreign_key"] = ForeignKey(foreign_key)

        if has_default:
            col_kwargs["default"] = default

        # Handle foreign key passed through special key above.
        if "foreign_key" in col_kwargs:
            fk = col_kwargs.pop("foreign_key")
            col = Column(col_type, fk, **col_kwargs)
        else:
            col = Column(col_type, **col_kwargs)

        cols[name] = col

    # If no explicit primary key found, emulate SQLModel's common "id" default.
    if not any(c.primary_key for c in cols.values()):
        if "id" in annotations and "id" in cols:
            cols["id"].primary_key = True
            cols["id"].nullable = False
        elif "id" in annotations and "id" not in cols:
            cols["id"] = Column(Integer, primary_key=True, nullable=False)

    return cols


def _build_relationships_for_model(cls: Type[Any]) -> Dict[str, Any]:
    rels: Dict[str, Any] = {}
    annotations = getattr(cls, "__annotations__", {}) or {}
    for name, ann in annotations.items():
        marker = getattr(cls, name, None)
        if isinstance(marker, tuple) and len(marker) == 2 and marker[0] == "__sqlmodel_relationship__":
            rel_kwargs = dict(marker[1])
            # Determine target from annotation
            tp = _optional_inner(ann)
            origin = get_origin(tp)
            if origin in (list, set, tuple):
                args = get_args(tp)
                target = args[0] if args else Any
            else:
                target = tp
            rels[name] = sa_relationship(target, **rel_kwargs)
    return rels


# --- Metaclass integrating Pydantic + SQLAlchemy declarative mapping ---

class SQLModelMetaclass(DeclarativeMeta):
    """
    Create a class that:
    - behaves as a Pydantic BaseModel
    - can be mapped by SQLAlchemy when table=True or __tablename__ is defined
    """
    def __new__(mcls, name, bases, namespace, **kwargs):
        table_flag = bool(namespace.pop("table", False))

        # Create a Pydantic model class first (this sets up __fields__, validation, etc).
        # Use BaseModel's metaclass directly, then retrofit SQLAlchemy mapping.
        pydantic_meta = BaseModel.__class__
        pyd_cls = pydantic_meta.__new__(pydantic_meta, name, bases, dict(namespace), **kwargs)

        # If this class should be a table, attach SQLAlchemy mapping attributes.
        is_table = table_flag or ("__tablename__" in namespace) or getattr(pyd_cls, "__tablename__", None) is not None
        if is_table and name != "SQLModel":
            if getattr(pyd_cls, "__tablename__", None) is None:
                setattr(pyd_cls, "__tablename__", name.lower())

            # Ensure registry + metadata exists
            if not hasattr(pyd_cls, "metadata"):
                setattr(pyd_cls, "metadata", _mapper_registry.metadata)

            cols = _build_columns_for_model(pyd_cls)
            for col_name, col in cols.items():
                if not hasattr(pyd_cls, col_name) or isinstance(getattr(pyd_cls, col_name), (int, str, float, bool, type(None))):
                    setattr(pyd_cls, col_name, col)
                else:
                    # If it's already something else (e.g. Column), keep as is.
                    if not isinstance(getattr(pyd_cls, col_name), Column):
                        setattr(pyd_cls, col_name, col)

            rels = _build_relationships_for_model(pyd_cls)
            for rel_name, rel in rels.items():
                setattr(pyd_cls, rel_name, rel)

            # Register mapping for SQLAlchemy declarative system.
            _mapper_registry.mapped(pyd_cls)

        return pyd_cls


class SQLModel(BaseModel, metaclass=SQLModelMetaclass):
    """
    Minimal SQLModel-like base.

    Supports:
    - Pydantic parsing/validation
    - SQLAlchemy ORM mapping when used with `table=True` or `__tablename__`.
    """
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

    # Common SQLModel attribute
    metadata = _mapper_registry.metadata

    def dict(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:  # type: ignore[override]
        return super().dict(*args, **kwargs)

    def json(self, *args: Any, **kwargs: Any) -> str:  # type: ignore[override]
        return super().json(*args, **kwargs)


# Provide a convenient sessionmaker factory (pattern used by some tests)
def _sessionmaker_for_engine(engine):
    return sessionmaker(bind=engine, class_=Session, expire_on_commit=False)