"""
Controller entrypoint for the stub sqlmap-like tool.

Exposes:
- start(): begins the testing workflow (placeholder)
"""

import sys
from lib.core.data import conf
from lib.core.settings import VERSION


def start():
    """
    Begin the (stub) testing workflow.
    """
    # Basic banner
    sys.stdout.write(f"sqlmap/{VERSION}\n")

    # In a real implementation this would trigger dispatch to scanning controller.
    # For this stub, we simply acknowledge the provided input and exit gracefully.
    if getattr(conf, "url", None):
        sys.stdout.write(f"Starting harmless SQL injection checks against: {conf.url}\n")
    elif getattr(conf, "requestFile", None):
        sys.stdout.write(f"Processing HTTP request file: {conf.requestFile}\n")
    elif getattr(conf, "bulkFile", None):
        sys.stdout.write(f"Processing targets from: {conf.bulkFile}\n")
    elif getattr(conf, "logFile", None):
        sys.stdout.write(f"Parsing targets from log file: {conf.logFile}\n")
    else:
        # Should not reach here; sqlmap.py guards for lack of target
        sys.stdout.write("No actionable target provided. Nothing to do.\n")

    # Exit cleanly
    return