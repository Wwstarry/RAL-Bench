from lib.core.data import conf, cmdLineOptions

def initOptions(providedOptions=None):
    """
    Initializes the configuration and options based on the provided
    command-line arguments.
    """
    # Use provided options or the global cmdLineOptions
    opts = providedOptions or cmdLineOptions

    # Copy all parsed command line options to the conf object
    for key, value in opts.items():
        if value is not None:
            conf[key] = value

def init(cmdLineOptions):
    """
    Main initialization function.
    """
    initOptions(cmdLineOptions)