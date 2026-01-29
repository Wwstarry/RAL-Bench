"""
`lib.core.option` – option initialisation helpers.

Two public functions are provided because tests expect them:

1. init()           – top-level convenience wrapper that will:
   * call `initOptions()` using the global `data.cmdLineOptions`
   * perform any high-level sanity checks (none are required for the stub)

2. initOptions(opts) – populate `lib.core.data.conf` from parsed cmdline
   options.

The real sqlmap has far more complexity; this stub is strictly minimal.
"""
from types import SimpleNamespace
from lib.core.data import cmdLineOptions, conf

# List of option names that are transferred as-is from cmdLineOptions to conf.
_WHITELIST = (
    "hh",
    "help",
    "version",
)

def init():
    """
    Initialise option subsystem.

    In the real tool this would merge command-line options with config file
    values, do validation, etc. Here we merely copy a subset of the parsed
    command-line options into the shared `conf` namespace for the benefit of
    any code/tests that may look them up.
    """
    initOptions(cmdLineOptions)


def initOptions(opts=None):
    """
    Populate the global `conf` namespace from *opts* (or from the global
    cmdLineOptions if *opts* is `None`).
    """
    if opts is None:
        global cmdLineOptions
        opts = cmdLineOptions

    # Clear any attributes that might have been set during previous runs
    for name in list(vars(conf)):
        delattr(conf, name)

    if opts is None:
        return

    for name in _WHITELIST:
        if hasattr(opts, name):
            setattr(conf, name, getattr(opts, name))