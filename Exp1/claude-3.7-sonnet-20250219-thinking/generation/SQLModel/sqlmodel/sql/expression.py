from typing import Type, TypeVar, Generic, List, Optional, Union, Any, Sequence
import sqlalchemy
from sqlalchemy import select as sa_select
from sqlalchemy.sql.expression import Select as SASelect
from sqlalchemy.orm import Query as SAQuery

from ..main import SQLModel

T = TypeVar("T", bound=SQLModel)


class Select(Generic[T]):
    def __init__(self, *entities: Type[T], _select_statement: Optional[SASelect] = None):
        self.entities = entities
        self._select_statement = _select_statement or sa_select(*entities)
    
    def where(self, *conditions: Any) -> "Select[T]":
        return Select(*self.entities, _select_statement=self._select_statement.where(*conditions))
    
    def order_by(self, *criteria: Any) -> "Select[T]":
        return Select(*self.entities, _select_statement=self._select_statement.order_by(*criteria))
    
    def offset(self, offset: int) -> "Select[T]":
        return Select(*self.entities, _select_statement=self._select_statement.offset(offset))
    
    def limit(self, limit: int) -> "Select[T]":
        return Select(*self.entities, _select_statement=self._select_statement.limit(limit))
    
    def join(self, *props: Any, **kwargs: Any) -> "Select[T]":
        return Select(*self.entities, _select_statement=self._select_statement.join(*props, **kwargs))
    
    def options(self, *options: Any) -> "Select[T]":
        return Select(*self.entities, _select_statement=self._select_statement.options(*options))
    
    def execution_options(self, **kwargs: Any) -> "Select[T]":
        return Select(*self.entities, _select_statement=self._select_statement.execution_options(**kwargs))
    
    def group_by(self, *criteria: Any) -> "Select[T]":
        return Select(*self.entities, _select_statement=self._select_statement.group_by(*criteria))
    
    def having(self, *criteria: Any) -> "Select[T]":
        return Select(*self.entities, _select_statement=self._select_statement.having(*criteria))
    
    def _raw_sql(self) -> SASelect:
        return self._select_statement


def select(*entities: Type[T]) -> Select[T]:
    """Create a SELECT statement for the specified entities."""
    return Select(*entities)