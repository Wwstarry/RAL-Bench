"""
List formatting utilities.
"""

from typing import List, Union


def oxford_comma(items: List[Union[str, int]], final_separator: str = "and") -> str:
    """
    Convert a list to a human-readable string with Oxford comma.
    
    Args:
        items: List of items to format
        final_separator: Word to use before the last item (default "and")
    
    Returns:
        Human-readable list string
    """
    items = [str(item) for item in items]
    
    if len(items) == 0:
        return ""
    elif len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return f"{items[0]} {final_separator} {items[1]}"
    else:
        return ", ".join(items[:-1]) + f", {final_separator} {items[-1]}"