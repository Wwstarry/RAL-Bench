"""
List humanization functions.
"""


def oxford_list(items, conjunction="and"):
    """
    Convert a list to a human-readable string with Oxford comma.
    
    Args:
        items: List of items to join
        conjunction: Conjunction word to use (default "and")
        
    Returns:
        String like "a, b, and c"
    """
    if not items:
        return ""
    
    items = [str(item) for item in items]
    
    if len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return items[0] + " " + conjunction + " " + items[1]
    else:
        return ", ".join(items[:-1]) + ", " + conjunction + " " + items[-1]