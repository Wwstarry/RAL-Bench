import re

def CleanText(text, strip=True, collapse=True, lower=False):
    """
    Cleans up text for safe display and searching.
    - strip: Remove leading/trailing whitespace.
    - collapse: Collapse internal whitespace.
    - lower: Convert to lowercase.
    """
    if not isinstance(text, str):
        text = str(text)
    if strip:
        text = text.strip()
    if collapse:
        text = re.sub(r'\s+', ' ', text)
    if lower:
        text = text.lower()
    return text

def base36(num):
    """
    Converts an integer to a base36 string.
    """
    if not isinstance(num, int):
        raise TypeError('base36() only works for integers')
    if num < 0:
        raise ValueError('base36() only works for positive integers')
    chars = '0123456789abcdefghijklmnopqrstuvwxyz'
    if num == 0:
        return '0'
    result = ''
    while num > 0:
        num, i = divmod(num, 36)
        result = chars[i] + result
    return result

def unbase36(s):
    """
    Converts a base36 string to an integer.
    """
    return int(s, 36)

def chunks(lst, n):
    """
    Yield successive n-sized chunks from lst.
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def dict_get_path(d, path, default=None):
    """
    Get a value from a nested dict using a list of keys.
    """
    for key in path:
        if isinstance(d, dict) and key in d:
            d = d[key]
        else:
            return default
    return d