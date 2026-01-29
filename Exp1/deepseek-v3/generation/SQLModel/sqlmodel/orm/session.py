"""Session-related functionality"""

from typing import Any, List, Optional, Type
from .. import SQLModel

class Session:
    """Enhanced session implementation"""
    
    def __init__(self, bind: Any = None, **kwargs: Any):
        self.bind = bind
        self._new_objects: List[SQLModel] = []
        self._dirty_objects: List[SQLModel] = []
        self._deleted_objects: List[SQLModel] = []
        self._committed_objects: List[SQLModel] = []
    
    def add(self, instance: SQLModel) -> None:
        """Add an instance to the session"""
        if instance not in self._new_objects and instance not in self._committed_objects:
            self._new_objects.append(instance)
    
    def add_all(self, instances: List[SQLModel]) -> None:
        """Add multiple instances to the session"""
        for instance in instances:
            self.add(instance)
    
    def commit(self) -> None:
        """Commit the transaction"""
        # Move new objects to committed
        self._committed_objects.extend(self._new_objects)
        self._new_objects.clear()
        
        # Clear dirty and deleted objects
        self._dirty_objects.clear()
        self._deleted_objects.clear()
    
    def rollback(self) -> None:
        """Rollback the transaction"""
        self._new_objects.clear()
        self._dirty_objects.clear()
        self._deleted_objects.clear()
    
    def refresh(self, instance: SQLModel) -> None:
        """Refresh the instance state"""
        # In pure Python implementation, this is mostly a no-op
        pass
    
    def query(self, entity: Type[SQLModel]) -> 'Query':
        """Create a query for the given entity"""
        return Query(entity, self)
    
    def exec(self, statement: Any) -> 'Result':
        """Execute a statement"""
        return Result(statement, self)
    
    def close(self) -> None:
        """Close the session"""
        self._new_objects.clear()
        self._dirty_objects.clear()
        self._deleted_objects.clear()
        self._committed_objects.clear()

class Query:
    """Query implementation"""
    
    def __init__(self, entity: Type[SQLModel], session: Session):
        self.entity = entity
        self.session = session
        self._filters = []
    
    def filter(self, *args, **kwargs) -> 'Query':
        """Add filter conditions"""
        self._filters.append((args, kwargs))
        return self
    
    def where(self, *args, **kwargs) -> 'Query':
        """Add where conditions"""
        return self.filter(*args, **kwargs)
    
    def all(self) -> List[SQLModel]:
        """Return all results"""
        # Get all objects of the entity type from session
        all_objects = [obj for obj in self.session._committed_objects 
                      if isinstance(obj, self.entity)]
        
        # Apply filters
        for filter_args, filter_kwargs in self._filters:
            filtered_objects = []
            for obj in all_objects:
                if self._matches_filters(obj, filter_args, filter_kwargs):
                    filtered_objects.append(obj)
            all_objects = filtered_objects
        
        return all_objects
    
    def first(self) -> Optional[SQLModel]:
        """Return first result"""
        results = self.all()
        return results[0] if results else None
    
    def one(self) -> SQLModel:
        """Return exactly one result"""
        results = self.all()
        if len(results) != 1:
            raise ValueError("Expected exactly one result")
        return results[0]
    
    def count(self) -> int:
        """Return count of results"""
        return len(self.all())
    
    def _matches_filters(self, obj: SQLModel, args: tuple, kwargs: dict) -> bool:
        """Check if object matches the given filters"""
        # Handle keyword arguments
        for key, value in kwargs.items():
            if not hasattr(obj, key):
                return False
            obj_value = getattr(obj, key)
            if obj_value != value:
                return False
        
        # Handle positional arguments (simple equality checks)
        for arg in args:
            if hasattr(arg, 'left') and hasattr(arg, 'right') and hasattr(arg, 'operator'):
                # Handle binary expressions
                left_name = arg.left.name if hasattr(arg.left, 'name') else str(arg.left)
                if hasattr(obj, left_name):
                    obj_value = getattr(obj, left_name)
                    if arg.operator == '=' and obj_value != arg.right:
                        return False
                    elif arg.operator == '!=' and obj_value == arg.right:
                        return False
                    # Add more operators as needed
        
        return True

class Result:
    """Result of statement execution"""
    
    def __init__(self, statement: Any, session: Session):
        self.statement = statement
        self.session = session
    
    def all(self) -> List[SQLModel]:
        """Return all results"""
        if hasattr(self.statement, 'model'):
            return self.session.query(self.statement.model).all()
        return []
    
    def first(self) -> Optional[SQLModel]:
        """Return first result"""
        results = self.all()
        return results[0] if results else None
    
    def one(self) -> SQLModel:
        """Return exactly one result"""
        results = self.all()
        if len(results) != 1:
            raise ValueError("Expected exactly one result")
        return results[0]
    
    def scalar(self) -> Any:
        """Return scalar result"""
        result = self.first()
        if result and hasattr(self.statement, 'selected_columns'):
            # Return first column value
            cols = self.statement.selected_columns
            if cols:
                return getattr(result, cols[0].name)
        return result