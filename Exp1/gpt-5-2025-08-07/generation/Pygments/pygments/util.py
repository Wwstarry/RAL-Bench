class ClassNotFound(Exception):
    """Raised when a requested lexer/formatter/style cannot be found."""
    pass

def text_type(s):
    # compatibility, just return str
    return str(s)

def bytes_type(b):
    return bytes(b)

def get_bool_opt(options, name, default=False):
    val = options.get(name, default)
    if isinstance(val, str):
        return val.lower() in ("1", "true", "yes", "on")
    return bool(val)