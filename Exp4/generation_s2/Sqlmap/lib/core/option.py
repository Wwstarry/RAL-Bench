# -*- coding: utf-8 -*-

"""
Options initialization.

The real sqlmap has extensive option processing. Here we keep a minimal,
test-friendly implementation while preserving function names and module paths:
- initOptions(argv): store raw argv into lib.core.data.cmdLineOptions
- init(parsed): populate lib.core.data.conf and lib.core.data.kb
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Iterable, Optional

from lib.core.data import cmdLineOptions, conf, kb


def initOptions(argv: Optional[Iterable[str]] = None) -> None:
    """
    Store command line arguments into global cmdLineOptions.
    """
    from lib.core import data as data_module

    if argv is None:
        argv = []
    data_module.cmdLineOptions = list(argv)


def init(parsedOptions: Any = None) -> None:
    """
    Initialize global configuration (conf) and runtime knowledge base (kb).
    """
    # conf/kb are SimpleNamespace instances, mutate in-place to preserve references.
    if not isinstance(conf, SimpleNamespace) or not isinstance(kb, SimpleNamespace):
        # Defensive: if something replaced these, recreate
        from lib.core import data as data_module

        data_module.conf = SimpleNamespace()
        data_module.kb = SimpleNamespace()

    # Defaults
    conf.batch = False
    conf.advancedHelp = False
    conf.url = None
    conf.data = None
    conf.method = None
    conf.cookie = None
    conf.level = 1
    conf.risk = 1
    conf.verbosity = 1
    conf.flushSession = False

    kb.initialized = True
    kb.errors = []
    kb.warnings = []
    kb.messages = []

    # Merge parsed options
    if parsedOptions is not None:
        # argparse Namespace supports vars()
        try:
            opts = vars(parsedOptions)
        except Exception:
            opts = {}

        for k, v in opts.items():
            setattr(conf, k, v)