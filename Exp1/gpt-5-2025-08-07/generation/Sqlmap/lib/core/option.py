"""
Options initialization for the stub sqlmap-like tool.

Exposes:
- initOptions(options): initialize default configuration and apply CLI options
- init(): finalize runtime configuration (no-op for stub, reserved for expansion)
"""

from lib.core.data import conf, cmdLineOptions
from lib.core.settings import VERSION


def initOptions(options):
    """
    Initialize default configuration and apply provided command-line options.
    """
    # defaults
    conf.clear()
    conf.version = VERSION
    conf.description = "sqlmap stub"
    conf.url = None
    conf.data = None
    conf.randomAgent = False
    conf.batch = False
    conf.disableColoring = False
    conf.requestFile = None
    conf.bulkFile = None
    conf.configFile = None
    conf.googleDork = None
    conf.threads = 1

    # keep original parsed options in global state
    # also update conf with known fields
    global cmdLineOptions
    cmdLineOptions = options

    if options is not None:
        # Target options
        conf.url = getattr(options, "url", conf.url)
        conf.data = getattr(options, "data", conf.data)
        conf.requestFile = getattr(options, "requestFile", conf.requestFile)
        conf.bulkFile = getattr(options, "bulkFile", conf.bulkFile)
        conf.logFile = getattr(options, "logFile", None)

        # General options
        conf.randomAgent = bool(getattr(options, "randomAgent", conf.randomAgent))
        conf.batch = bool(getattr(options, "batch", conf.batch))
        conf.disableColoring = bool(getattr(options, "disableColoring", conf.disableColoring))

        # Misc options
        conf.configFile = getattr(options, "configFile", conf.configFile)
        conf.googleDork = getattr(options, "googleDork", conf.googleDork)
        conf.threads = getattr(options, "threads", conf.threads)


def init():
    """
    Finalize configuration. For stub implementation this is a no-op placeholder.
    """
    # In real sqlmap, this would process conf and set additional defaults and runtime values.
    # Here we leave it as a placeholder for compatibility.
    return