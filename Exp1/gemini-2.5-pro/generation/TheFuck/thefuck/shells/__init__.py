def get_alias(alias_name='fuck'):
    """
    Returns a generic alias string for shell integration.
    """
    return "alias {}='eval $(thefuck $(fc -ln -1))'".format(alias_name)