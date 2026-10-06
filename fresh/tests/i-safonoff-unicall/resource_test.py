import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'unicall'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'CoalescedFunction', 'kind': 'object', 'signature': ''}, {'name': 'Coalescer', 'kind': 'object', 'signature': ''}, {'name': 'UnhashableArgumentsError', 'kind': 'object', 'signature': ''}, {'name': 'unicall', 'kind': 'object', 'signature': ''}, {'name': 'Backend', 'kind': 'object', 'signature': ''}, {'name': 'DistributedCoalescer', 'kind': 'object', 'signature': ''}, {'name': 'JSONSerializer', 'kind': 'object', 'signature': ''}, {'name': 'RemoteFlightError', 'kind': 'object', 'signature': ''}, {'name': 'Serializer', 'kind': 'object', 'signature': ''}, {'name': 'UnserializableResultError', 'kind': 'object', 'signature': ''}, {'name': 'distributed', 'kind': 'object', 'signature': ''}, {'name': 'Metrics', 'kind': 'object', 'signature': ''}, {'name': 'Stats', 'kind': 'object', 'signature': ''}, {'name': 'stable_hash', 'kind': 'object', 'signature': ''}]
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

