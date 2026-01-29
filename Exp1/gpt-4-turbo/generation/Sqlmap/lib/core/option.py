from lib.core.data import conf, cmdLineOptions

def initOptions(cmdLineOptions):
    # Initialize conf.options from cmdLineOptions
    conf.options = {}
    for k in dir(cmdLineOptions):
        if not k.startswith("_"):
            v = getattr(cmdLineOptions, k)
            conf.options[k] = v

def init(cmdLineOptions):
    # Set conf.initialized flag
    conf.initialized = True