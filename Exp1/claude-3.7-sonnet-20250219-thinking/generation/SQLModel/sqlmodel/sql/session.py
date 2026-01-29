from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Generator, Iterator, Callable
import contextlib
from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session as SASession, sessionmaker
from sqlalchemy.engine import Engine

from ..main import SQLModelMetaData, SQLModel
from .expression import Select

T = TypeVar("T", bound=SQLModel)


class Session(SASession):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
    
    def exec(self, statement: Union[Select, Any]) -> "Result":
        if isinstance(statement, Select):
            return Result(self.execute(statement._raw_sql()))
        return Result(self.execute(statement))
    
    def get(self, model_class: Type[T], id_value: Any) -> Optional[T]:
        return self.query(model_class).get(id_value)
    
    def add(self, instance: SQLModel) -> None:
        super().add(instance)
    
    def add_all(self, instances: List[SQLModel]) -> None:
        super().add_all(instances)
    
    def delete(self, instance: SQLModel) -> None:
        super().delete(instance)
    
    def commit(self) -> None:
        super().commit()
    
    def rollback(self) -> None:
        super().rollback()
    
    def refresh(self, instance: SQLModel) -> None:
        super().refresh(instance)
    
    def close(self) -> None:
        super().close()


class Result(Iterator[T]):
    def __init__(self, result: Any):
        self.result = result
    
    def __iter__(self) -> "Result":
        return self
    
    def __next__(self) -> T:
        try:
            return next(self.result)
        except StopIteration:
            raise
    
    def all(self) -> List[T]:
        return list(self)
    
    def first(self) -> Optional[T]:
        try:
            return next(self)
        except StopIteration:
            return None
    
    def one(self) -> T:
        items = list(self)
        if not items:
            raise Exception("No row was found")
        if len(items) > 1:
            raise Exception("Multiple rows were found")
        return items[0]
    
    def one_or_none(self) -> Optional[T]:
        items = list(self)
        if not items:
            return None
        if len(items) > 1:
            raise Exception("Multiple rows were found")
        return items[0]


class Engine:
    def __init__(self, engine: Any):
        self.engine = engine
    
    def connect(self) -> Any:
        return self.engine.connect()
    
    def begin(self) -> Any:
        return self.engine.begin()
    
    def dispose(self) -> None:
        self.engine.dispose()


_engine_session_factory = None
engine = None


def create_engine(url: str, **kwargs: Any) -> Engine:
    global _engine_session_factory, engine
    engine_obj = sa_create_engine(url, **kwargs)
    engine = Engine(engine_obj)
    _engine_session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine_obj,
        class_=Session,
    )
    return engine


def create_session() -> Session:
    if _engine_session_factory is None:
        raise Exception("Engine not initialized. Call create_engine first.")
    return _engine_session_factory()


@contextlib.contextmanager
def Session(bind=None) -> Generator[Session, None, None]:
    if bind is None and _engine_session_factory is None:
        raise Exception("Engine not initialized. Call create_engine first.")
    
    if bind is not None:
        session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=bind,
            class_=Session,
        )
        session = session_factory()
    else:
        session = create_session()
    
    try:
        yield session
    finally:
        session.close()