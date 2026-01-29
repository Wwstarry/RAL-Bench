"""
Shared runtime state for sqlmap-like interface.

The real sqlmap uses rich structures; for this compatibility layer we provide
simple dict-like objects that are safe for the test suite and CLI invocations.
"""

# Parsed command line options (dict)
cmdLineOptions = {}

# Global configuration (dict)
conf = {}

# Knowledge base / runtime state (dict)
kb = {}