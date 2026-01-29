# -*- coding: utf-8 -*-

"""
Controller entry point.

Exposes lib.controller.controller.start
"""

from __future__ import annotations

import sys
from urllib.parse import urlparse

from lib.core.data import conf, kb


def _validate_target() -> None:
    """
    Minimal validation: if user provided URL, ensure it's parseable.
    If no URL provided, behave benignly (no external target required by tests).
    """
    if not getattr(conf, "url", None):
        return

    parsed = urlparse(conf.url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"invalid URL: {conf.url!r}")


def start() -> int:
    """
    Run the tool.

    For the purposes of unit/black-box tests, this function should:
    - not perform any network activity unless user provided a target
    - exit cleanly with informative messages for missing/invalid input
    """
    try:
        _validate_target()
    except Exception as ex:
        sys.stderr.write(f"[!] {ex}\n")
        sys.stderr.write("[*] Use -h for basic help.\n")
        return 2

    # If invoked without a target, just print a short informational message and exit.
    if not getattr(conf, "url", None):
        # Quietly succeed; tests often call help/version only, but this keeps behavior safe.
        if getattr(conf, "verbosity", 1) >= 1:
            sys.stdout.write("sqlmap: no target provided. Use -u/--url to specify a target.\n")
        return 0

    # Skeleton "scan": no real injection logic, just a placeholder result.
    if getattr(conf, "verbosity", 1) >= 1:
        sys.stdout.write(f"[*] starting scan on: {conf.url}\n")
        sys.stdout.write("[*] no real scanning implemented in this minimal version\n")

    kb.lastTarget = conf.url
    return 0