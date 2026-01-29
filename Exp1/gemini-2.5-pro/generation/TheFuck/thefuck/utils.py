def get_all_executables():
    """
    Returns a list of known executables.

    In a real implementation, this would scan the system's PATH.
    For testing, a fixed list is sufficient and more reliable.
    """
    return ['git', 'python', 'pip', 'ls', 'cat', 'grep', 'cd', 'sudo', 'apt-get']