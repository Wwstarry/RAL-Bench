from __future__ import annotations

from lib.core.data import cmdLineOptions as _cmdLineOptions_global, conf, kb
from lib.core.data import AttribDict
from lib.core.settings import VERSION, DESCRIPTION
from lib.parse.cmdline import cmdLineParser

# We will update lib.core.data.cmdLineOptions by importing the module (not just the name)
import lib.core.data as data


def init(argv=None):
    """
    Early initialization: parse command line and store into global cmdLineOptions.
    """
    opts = cmdLineParser(argv)
    data.cmdLineOptions = opts
    return opts


def initOptions(cmdLineOptions=None):
    """
    Initialize global configuration (conf) and knowledge base (kb) from parsed options.
    Safe to call even for help/version paths (though those exit before reaching here).
    """
    if cmdLineOptions is None:
        cmdLineOptions = getattr(data, "cmdLineOptions", None)

    # Reset/ensure basic metadata
    conf.version = VERSION
    conf.description = DESCRIPTION

    # Initialize a few common fields with safe defaults
    if cmdLineOptions is None:
        # Keep conf/kb usable even if called without parsing
        conf.url = None
        conf.data = None
        conf.param = None
        conf.batch = False
        conf.verbose = 0
        conf.risk = 1
        conf.level = 1
        conf.randomAgent = False
        conf.threads = 1
        conf.tamper = None
    else:
        conf.url = getattr(cmdLineOptions, "url", None)
        conf.data = getattr(cmdLineOptions, "data", None)
        conf.param = getattr(cmdLineOptions, "param", None)
        conf.batch = bool(getattr(cmdLineOptions, "batch", False))
        conf.verbose = int(getattr(cmdLineOptions, "verbose", 0) or 0)
        conf.risk = int(getattr(cmdLineOptions, "risk", 1) or 1)
        conf.level = int(getattr(cmdLineOptions, "level", 1) or 1)
        conf.randomAgent = bool(getattr(cmdLineOptions, "random_agent", False))
        conf.threads = int(getattr(cmdLineOptions, "threads", 1) or 1)
        conf.tamper = getattr(cmdLineOptions, "tamper", None)

    # Minimal knowledge base placeholders
    kb.multipleTargets = False
    kb.stopped = False
    kb.errors = []

    return conf