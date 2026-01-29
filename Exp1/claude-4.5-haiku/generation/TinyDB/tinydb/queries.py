"""
Query module for building filter conditions.
"""

from typing import Any, Callable, Dict


class QueryInstance:
    """
    Represents a query condition that can be used to filter documents.
    """

    def __init__(self, field: str):
        """
        Initialize a query instance for a specific field.

        Args:
            field: Field name to query
        """
        self.field = field

    def __eq__(self, value: Any) -> Callable[[Dict[str, Any]], bool]:
        """
        Create an equality condition.

        Args:
            value: Value to compare

        Returns:
            Condition function
        """
        def condition(doc: Dict[str, Any]) -> bool:
            return doc.get(self.field) == value
        return condition

    def __ne__(self, value: Any) -> Callable[[Dict[str, Any]], bool]:
        """
        Create a not-equal condition.

        Args:
            value: Value to compare

        Returns:
            Condition function
        """
        def condition(doc: Dict[str, Any]) -> bool:
            return doc.get(self.field) != value
        return condition

    def __lt__(self, value: Any) -> Callable[[Dict[str, Any]], bool]:
        """
        Create a less-than condition.

        Args:
            value: Value to compare

        Returns:
            Condition function
        """
        def condition(doc: Dict[str, Any]) -> bool:
            field_value = doc.get(self.field)
            return field_value is not None and field_value < value
        return condition

    def __le__(self, value: Any) -> Callable[[Dict[str, Any]], bool]:
        """
        Create a less-than-or-equal condition.

        Args:
            value: Value to compare

        Returns:
            Condition function
        """
        def condition(doc: Dict[str, Any]) -> bool:
            field_value = doc.get(self.field)
            return field_value is not None and field_value <= value
        return condition

    def __gt__(self, value: Any) -> Callable[[Dict[str, Any]], bool]:
        """
        Create a greater-than condition.

        Args:
            value: Value to compare

        Returns:
            Condition function
        """
        def condition(doc: Dict[str, Any]) -> bool:
            field_value = doc.get(self.field)
            return field_value is not None and field_value > value
        return condition

    def __ge__(self, value: Any) -> Callable[[Dict[str, Any]], bool]:
        """
        Create a greater-than-or-equal condition.

        Args:
            value: Value to compare

        Returns:
            Condition function
        """
        def condition(doc: Dict[str, Any]) -> bool:
            field_value = doc.get(self.field)
            return field_value is not None and field_value >= value
        return condition

    def exists(self) -> Callable[[Dict[str, Any]], bool]:
        """
        Create a condition checking if field exists.

        Returns:
            Condition function
        """
        def condition(doc: Dict[str, Any]) -> bool:
            return self.field in doc
        return condition

    def contains(self, value: Any) -> Callable[[Dict[str, Any]], bool]:
        """
        Create a condition checking if field contains value.

        Args:
            value: Value to check for

        Returns:
            Condition function
        """
        def condition(doc: Dict[str, Any]) -> bool:
            field_value = doc.get(self.field)
            if isinstance(field_value, (list, str)):
                return value in field_value
            return False
        return condition

    def test(self, func: Callable[[Any], bool]) -> Callable[[Dict[str, Any]], bool]:
        """
        Create a condition using a custom test function.

        Args:
            func: Function that tests the field value

        Returns:
            Condition function
        """
        def condition(doc: Dict[str, Any]) -> bool:
            field_value = doc.get(self.field)
            return func(field_value)
        return condition


class Query:
    """
    Factory for creating query conditions.
    """

    def __getattr__(self, field: str) -> QueryInstance:
        """
        Create a query instance for a field.

        Args:
            field: Field name

        Returns:
            QueryInstance for the field
        """
        return QueryInstance(field)


def and_(*conditions: Callable[[Dict[str, Any]], bool]) -> Callable[[Dict[str, Any]], bool]:
    """
    Combine multiple conditions with AND logic.

    Args:
        *conditions: Conditions to combine

    Returns:
        Combined condition function
    """
    def combined(doc: Dict[str, Any]) -> bool:
        return all(cond(doc) for cond in conditions)
    return combined


def or_(*conditions: Callable[[Dict[str, Any]], bool]) -> Callable[[Dict[str, Any]], bool]:
    """
    Combine multiple conditions with OR logic.

    Args:
        *conditions: Conditions to combine

    Returns:
        Combined condition function
    """
    def combined(doc: Dict[str, Any]) -> bool:
        return any(cond(doc) for cond in conditions)
    return combined


def not_(condition: Callable[[Dict[str, Any]], bool]) -> Callable[[Dict[str, Any]], bool]:
    """
    Negate a condition.

    Args:
        condition: Condition to negate

    Returns:
        Negated condition function
    """
    def negated(doc: Dict[str, Any]) -> bool:
        return not condition(doc)
    return negated