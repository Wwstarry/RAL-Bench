"""
lists.py

Human-readable textual representations of lists.
"""

def natural_list(values, conj='and'):
    """
    Returns a naturally joined list string. For example:
        ['apples', 'bananas', 'pears'] -> 'apples, bananas and pears'
    """
    values = list(values)
    if not values:
        return ''
    if len(values) == 1:
        return str(values[0])
    return ', '.join(str(x) for x in values[:-1]) + f' {conj} ' + str(values[-1])