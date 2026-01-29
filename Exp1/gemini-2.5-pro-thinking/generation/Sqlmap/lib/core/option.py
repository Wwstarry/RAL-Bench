from lib.core.data import cmdLineOptions, conf, kb

def initOptions(dict_):
    """
    Initializes the cmdLineOptions object with parsed arguments.
    """
    cmdLineOptions.update(dict_)

def init():
    """
    Initializes the global configuration (conf) and knowledge base (kb)
    objects based on the command-line options.
    """
    # In a real tool, this function would set up default values,
    # configure logging, create temporary directories, etc.
    # Here, we simply copy the command line options into the 'conf' object.
    for key, value in cmdLineOptions.items():
        if value is not None:
            conf[key] = value

    # Initialize the knowledge base with some default structures.
    kb.injections = []
    kb.tested_params = set()
    kb.targets = set()