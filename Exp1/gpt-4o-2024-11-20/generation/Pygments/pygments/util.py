def get_bool_opt(options, key, default=False):
    """
    Get a boolean option from a dictionary.

    :param options: The dictionary of options.
    :param key: The key to look up.
    :param default: The default value if the key is not found.
    :return: The boolean value of the option.
    """
    return bool(options.get(key, default))