"""
Query module for TinyDB.
"""
from typing import Any, Callable, Dict


class Query:
    """Query class for building search conditions."""
    
    def __init__(self):
        self._conditions = []
    
    def __call__(self, doc: Dict) -> bool:
        """
        Test if document matches all conditions.
        
        Args:
            doc: Document to test
            
        Returns:
            True if document matches all conditions
        """
        for condition in self._conditions:
            if not condition(doc):
                return False
        return True
    
    def _add_condition(self, field: str, value: Any, op: str) -> 'Query':
        """
        Add a condition to the query.
        
        Args:
            field: Field name
            value: Value to compare
            op: Comparison operator
            
        Returns:
            Self for chaining
        """
        if op == '==':
            condition = lambda doc: doc.get(field) == value
        elif op == '!=':
            condition = lambda doc: doc.get(field) != value
        elif op == '>':
            condition = lambda doc: doc.get(field) > value
        elif op == '>=':
            condition = lambda doc: doc.get(field) >= value
        elif op == '<':
            condition = lambda doc: doc.get(field) < value
        elif op == '<=':
            condition = lambda doc: doc.get(field) <= value
        elif op == 'in':
            condition = lambda doc: doc.get(field) in value
        elif op == 'not in':
            condition = lambda doc: doc.get(field) not in value
        else:
            raise ValueError(f"Unsupported operator: {op}")
        
        self._conditions.append(condition)
        return self
    
    def __getattr__(self, name: str) -> 'QueryField':
        """
        Get a query field.
        
        Args:
            name: Field name
            
        Returns:
            QueryField instance
        """
        return QueryField(name, self)
    
    def __and__(self, other: 'Query') -> 'Query':
        """
        Combine queries with AND.
        
        Args:
            other: Other query
            
        Returns:
            New combined query
        """
        new_query = Query()
        new_query._conditions = self._conditions + other._conditions
        return new_query
    
    def __or__(self, other: 'Query') -> 'Query':
        """
        Combine queries with OR.
        
        Args:
            other: Other query
            
        Returns:
            New combined query
        """
        def or_condition(doc: Dict) -> bool:
            return self(doc) or other(doc)
        
        new_query = Query()
        new_query._conditions = [or_condition]
        return new_query


class QueryField:
    """Query field for building conditions."""
    
    def __init__(self, name: str, query: Query):
        self.name = name
        self.query = query
    
    def __eq__(self, value: Any) -> Query:
        return self.query._add_condition(self.name, value, '==')
    
    def __ne__(self, value: Any) -> Query:
        return self.query._add_condition(self.name, value, '!=')
    
    def __gt__(self, value: Any) -> Query:
        return self.query._add_condition(self.name, value, '>')
    
    def __ge__(self, value: Any) -> Query:
        return self.query._add_condition(self.name, value, '>=')
    
    def __lt__(self, value: Any) -> Query:
        return self.query._add_condition(self.name, value, '<')
    
    def __le__(self, value: Any) -> Query:
        return self.query._add_condition(self.name, value, '<=')
    
    def in_(self, value: list) -> Query:
        return self.query._add_condition(self.name, value, 'in')
    
    def not_in(self, value: list) -> Query:
        return self.query._add_condition(self.name, value, 'not in')