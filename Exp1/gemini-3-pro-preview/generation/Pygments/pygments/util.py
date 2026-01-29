class ClassNotFound(ValueError):
    """Raised if one of the lookup functions didn't find a matching class."""
    pass

class OptionError(Exception):
    pass

def get_choice_opt(options, optname, allowed, default=None, normcase=False):
    string = options.get(optname, default)
    if normcase:
        string = string.lower()
    if string not in allowed:
        raise OptionError('Value for option %s must be one of %s' %
                          (optname, ', '.join(map(str, allowed))))
    return string

def get_bool_opt(options, optname, default=None):
    string = options.get(optname, default)
    if isinstance(string, bool):
        return string
    if isinstance(string, int):
        return bool(string)
    if not isinstance(string, str):
        return default
    string = string.lower()
    if string in ('1', 'yes', 'true', 'on'):
        return True
    if string in ('0', 'no', 'false', 'off'):
        return False
    return default