from typing import Any, Callable, Dict, List, Union
import re

class Query:
    """
    Query class for building queries.
    """
    
    def __init__(self):
        self._test = lambda doc: True
    
    def __call__(self, doc: Dict) -> bool:
        return self._test(doc)
    
    def __and__(self, other):
        query = Query()
        query._test = lambda doc: self(doc) and other(doc)
        return query
    
    def __or__(self, other):
        query = Query()
        query._test = lambda doc: self(doc) or other(doc)
        return query
    
    def __invert__(self):
        query = Query()
        query._test = lambda doc: not self(doc)
        return query
    
    def test(self, key: str, test: Callable[[Any], bool]) -> 'Query':
        """
        Test a field with a function.
        
        Args:
            key: The field name.
            test: The test function.
            
        Returns:
            A Query instance.
        """
        def _test(doc):
            if key not in doc:
                return False
            return test(doc[key])
        
        query = Query()
        query._test = _test
        return query
    
    def matches(self, key: str, regex: str) -> 'Query':
        """
        Test if a field matches a regular expression.
        
        Args:
            key: The field name.
            regex: The regular expression.
            
        Returns:
            A Query instance.
        """
        return self.test(key, lambda value: bool(re.match(regex, value)))
    
    def search(self, key: str, regex: str) -> 'Query':
        """
        Test if a field contains a regex match.
        
        Args:
            key: The field name.
            regex: The regular expression.
            
        Returns:
            A Query instance.
        """
        return self.test(key, lambda value: bool(re.search(regex, value)))
    
    def exists(self, key: str) -> 'Query':
        """
        Test if a field exists.
        
        Args:
            key: The field name.
            
        Returns:
            A Query instance.
        """
        query = Query()
        query._test = lambda doc: key in doc
        return query
    
    def equals(self, key: str, value: Any) -> 'Query':
        """
        Test if a field equals a value.
        
        Args:
            key: The field name.
            value: The value to compare.
            
        Returns:
            A Query instance.
        """
        return self.test(key, lambda val: val == value)
    
    def not_equals(self, key: str, value: Any) -> 'Query':
        """
        Test if a field does not equal a value.
        
        Args:
            key: The field name.
            value: The value to compare.
            
        Returns:
            A Query instance.
        """
        return self.test(key, lambda val: val != value)
    
    def greater(self, key: str, value: Any) -> 'Query':
        """
        Test if a field is greater than a value.
        
        Args:
            key: The field name.
            value: The value to compare.
            
        Returns:
            A Query instance.
        """
        return self.test(key, lambda val: val > value)
    
    def greater_equals(self, key: str, value: Any) -> 'Query':
        """
        Test if a field is greater than or equal to a value.
        
        Args:
            key: The field name.
            value: The value to compare.
            
        Returns:
            A Query instance.
        """
        return self.test(key, lambda val: val >= value)
    
    def less(self, key: str, value: Any) -> 'Query':
        """
        Test if a field is less than a value.
        
        Args:
            key: The field name.
            value: The value to compare.
            
        Returns:
            A Query instance.
        """
        return self.test(key, lambda val: val < value)
    
    def less_equals(self, key: str, value: Any) -> 'Query':
        """
        Test if a field is less than or equal to a value.
        
        Args:
            key: The field name.
            value: The value to compare.
            
        Returns:
            A Query instance.
        """
        return self.test(key, lambda val: val <= value)
    
    def one_of(self, key: str, values: List[Any]) -> 'Query':
        """
        Test if a field is one of a list of values.
        
        Args:
            key: The field name.
            values: The values to compare.
            
        Returns:
            A Query instance.
        """
        return self.test(key, lambda val: val in values)

def where(key: str) -> Query:
    """
    Create a new query for a field.
    
    Args:
        key: The field name.
        
    Returns:
        A Query instance.
    """
    query = Query()
    return query