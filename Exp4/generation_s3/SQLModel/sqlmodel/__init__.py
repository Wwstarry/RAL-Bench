"""
A tiny, pure-Python subset of SQLModel, implemented for educational/testing use.

Non-goals:
- No SQLAlchemy dependency
- No Pydantic dependency
- No real SQL execution; in-memory engine only
"""

from .main import SQLModel
from .fields import Field
from .sql import select
from .orm import Relationship
from .engine import Engine, create_engine
from .session import Session

__all__ = [
    "SQLModel",
    "Field",
    "Relationship",
    "select",
    "Session",
    "Engine",
    "create_engine",
]