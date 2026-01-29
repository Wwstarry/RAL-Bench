from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel, Field as PydanticField, ValidationError
from pydantic.main import ModelMetaclass
from sqlalchemy import Column, Integer, String, create_engine, MetaData, Table, select as sa_select
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session as SQLAlchemySession

# Base class for SQLAlchemy ORM
Base = declarative_base()
metadata = MetaData()

# Type variable for SQLModel
T = TypeVar("T", bound="SQLModel")

class SQLModelMetaclass(ModelMetaclass):
    def __new__(cls, name, bases, namespace, **kwargs):
        # Handle SQLAlchemy table inheritance
        if "table" not in namespace and any(issubclass(base, SQLModel) for base in bases):
            namespace["__tablename__"] = namespace.get("__tablename__", name.lower())
            namespace["__table_args__"] = namespace.get("__table_args__", {})
        return super().__new__(cls, name, bases, namespace, **kwargs)

class SQLModel(BaseModel, Base, metaclass=SQLModelMetaclass):
    id: Optional[int] = PydanticField(default=None, primary_key=True)

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        return super().dict(*args, **kwargs)

    def json(self, *args, **kwargs) -> str:
        return super().json(*args, **kwargs)

    @classmethod
    def from_orm(cls: Type[T], obj: Any) -> T:
        return super().from_orm(obj)

    @classmethod
    def create_table(cls, engine):
        cls.__table__.create(bind=engine, checkfirst=True)

    @classmethod
    def select(cls):
        return sa_select(cls)

def Field(*args, **kwargs):
    return PydanticField(*args, **kwargs)

def select(*args, **kwargs):
    return sa_select(*args, **kwargs)

def Relationship(*args, **kwargs):
    return relationship(*args, **kwargs)

# Session and engine utilities
def create_engine_and_session(database_url: str):
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return engine, Session

class Session:
    def __init__(self, session: SQLAlchemySession):
        self._session = session

    def add(self, instance: SQLModel):
        self._session.add(instance)

    def commit(self):
        self._session.commit()

    def refresh(self, instance: SQLModel):
        self._session.refresh(instance)

    def query(self, model: Type[SQLModel]):
        return self._session.query(model)

    def close(self):
        self._session.close()