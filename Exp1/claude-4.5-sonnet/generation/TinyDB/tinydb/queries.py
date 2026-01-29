"""
Query builder for TinyDB
"""

from typing import Any, Callable, List


class Query:
    """
    Query builder for creating search conditions
    """
    
    def __init__(self, path: List[str] = None):
        """
        Initialize a query
        
        Args:
            path: Path to the field (for nested queries)
        """
        self._path = path or []
    
    def __getattr__(self, key: str) -> 'Query':
        """
        Access a field in the document
        
        Args:
            key: Field name
            
        Returns:
            New Query instance with updated path
        """
        return Query(self._path + [key])
    
    def _get_value(self, doc: dict) -> Any:
        """
        Get the value at the query path from a document
        
        Args:
            doc: Document to extract value from
            
        Returns:
            Value at the path or None if not found
        """
        value = doc
        for key in self._path:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    def __eq__(self, other: Any) -> Callable:
        """Equal comparison"""
        def test(doc):
            return self._get_value(doc) == other
        return test
    
    def __ne__(self, other: Any) -> Callable:
        """Not equal comparison"""
        def test(doc):
            return self._get_value(doc) != other
        return test
    
    def __lt__(self, other: Any) -> Callable:
        """Less than comparison"""
        def test(doc):
            value = self._get_value(doc)
            return value is not None and value < other
        return test
    
    def __le__(self, other: Any) -> Callable:
        """Less than or equal comparison"""
        def test(doc):
            value = self._get_value(doc)
            return value is not None and value <= other
        return test
    
    def __gt__(self, other: Any) -> Callable:
        """Greater than comparison"""
        def test(doc):
            value = self._get_value(doc)
            return value is not None and value > other
        return test
    
    def __ge__(self, other: Any) -> Callable:
        """Greater than or equal comparison"""
        def test(doc):
            value = self._get_value(doc)
            return value is not None and value >= other
        return test
    
    def exists(self) -> Callable:
        """Check if field exists"""
        def test(doc):
            return self._get_value(doc) is not None
        return test
    
    def matches(self, pattern: str) -> Callable:
        """
        Check if field matches a regex pattern
        
        Args:
            pattern: Regex pattern to match
            
        Returns:
            Test function
        """
        import re
        regex = re.compile(pattern)
        
        def test(doc):
            value = self._get_value(doc)
            return value is not None and regex.search(str(value)) is not None
        return test
    
    def one_of(self, items: List[Any]) -> Callable:
        """
        Check if field value is in a list
        
        Args:
            items: List of possible values
            
        Returns:
            Test function
        """
        def test(doc):
            return self._get_value(doc) in items
        return test
    
    def test(self, func: Callable[[Any], bool]) -> Callable:
        """
        Apply a custom test function to the field value
        
        Args:
            func: Function that takes the field value and returns bool
            
        Returns:
            Test function
        """
        def test(doc):
            value = self._get_value(doc)
            return func(value)
        return test


def where(key: str) -> Query:
    """
    Create a query for a field
    
    Args:
        key: Field name
        
    Returns:
        Query instance
    """
    return Query([key])