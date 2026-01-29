# -*- coding: utf-8 -*-

"""
Shared runtime state.

The reference sqlmap exposes mutable global objects used across modules:
- cmdLineOptions: parsed/initial CLI options (or placeholder)
- conf: runtime configuration (merged defaults + user-provided options)
- kb: knowledge base / runtime scratch pad
"""

from types import SimpleNamespace

# Placeholder for raw cmdline options (e.g., argv list or parsed Namespace)
cmdLineOptions = None

# Runtime configuration container
conf = SimpleNamespace()

# Knowledge base container
kb = SimpleNamespace()