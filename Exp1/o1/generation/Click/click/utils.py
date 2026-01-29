# click/utils.py
# Utility functions that might be helpful throughout the library.

def make_str(s):
    """
    Ensure the value is a string, decoding bytes if needed.
    """
    if isinstance(s, bytes):
        return s.decode("utf-8", "replace")
    return str(s)