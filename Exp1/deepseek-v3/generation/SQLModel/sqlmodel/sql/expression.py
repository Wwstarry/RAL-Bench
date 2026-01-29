"""SQL expression components"""

from typing import Any, List, Optional, Union

class ColumnElement:
    """Base class for column expressions"""
    
    def __init__(self, name: str):
        self.name = name
    
    def __eq__(self, other: Any) -> 'BinaryExpression':
        return BinaryExpression(self, other, '=')
    
    def __ne__(self, other: Any) -> 'BinaryExpression':
        return BinaryExpression(self, other, '!=')
    
    def __lt__(self, other: Any) -> 'BinaryExpression':
        return BinaryExpression(self, other, '<')
    
    def __le__(self, other: Any) -> 'BinaryExpression':
        return BinaryExpression(self, other, '<=')
    
    def __gt__(self, other: Any) -> 'BinaryExpression':
        return BinaryExpression(self, other, '>')
    
    def __ge__(self, other: Any) -> 'BinaryExpression':
        return BinaryExpression(self, other, '>=')

class BinaryExpression:
    """Binary expression like column == value"""
    
    def __init__(self, left: Any, right: Any, operator: str):
        self.left = left
        self.right = right
        self.operator = operator

class Column(ColumnElement):
    """SQL column representation"""
    
    def __init__(self, name: str, type_: Any = None, primary_key: bool = False):
        super().__init__(name)
        self.type = type_
        self.primary_key = primary_key

class and_:
    """AND conjunction"""
    
    def __init__(self, *clauses: Any):
        self.clauses = clauses

class or_:
    """OR conjunction"""
    
    def __init__(self, *clauses: Any):
        self.clauses = clauses

class not_:
    """NOT operator"""
    
    def __init__(self, clause: Any):
        self.clause = clause