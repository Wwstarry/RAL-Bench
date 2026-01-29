"""
Minimal option initialization functions providing sqlmap-compatible symbols:
- init
- initOptions
"""

from lib.core.data import conf, kb


def initOptions(options):
    """
    Initialize default configuration values based on parsed command line options.
    """
    if options is None:
        options = {}

    # Keep a copy in conf and normalize a few values
    conf.clear()
    conf.update(options)

    # Set defaults expected by benign invocations
    conf.setdefault("batch", False)
    conf.setdefault("verbosity", 1)
    conf.setdefault("advancedHelp", False)
    conf.setdefault("url", None)


def init():
    """
    Initialize shared runtime state.
    """
    kb.clear()
    kb["initialized"] = True
    kb.setdefault("errors", [])