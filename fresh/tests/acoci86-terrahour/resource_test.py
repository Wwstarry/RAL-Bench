import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'terrahour.alerts'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'resolve_place', 'kind': 'function', 'signature': '(st, name)'}, {'name': 'parse_alert', 'kind': 'function', 'signature': '(text, st)'}, {'name': 'alert_city', 'kind': 'function', 'signature': '(a)'}, {'name': 'notify', 'kind': 'function', 'signature': '(text)'}, {'name': 'check_alerts', 'kind': 'function', 'signature': '(st, live)'}]
CONSTANTS = {}


def load_module():
    repo = Path(os.environ["RACB_REPO_ROOT"]).resolve()
    root = repo if MODULE_ROOT == "." else repo / MODULE_ROOT
    sys.path.insert(0, str(root))
    return importlib.import_module(MODULE)


def test_public_surface_is_finite():
    module = load_module()
    names = dir(module)
    assert MODULE.split(".")[-1] in module.__name__
    assert len(names) < 10000

