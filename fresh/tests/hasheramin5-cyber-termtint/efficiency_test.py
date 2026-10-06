import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'termtint'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'colored', 'kind': 'object', 'signature': ''}, {'name': 'disable_color', 'kind': 'object', 'signature': ''}, {'name': 'enable_color', 'kind': 'object', 'signature': ''}, {'name': 'is_color_enabled', 'kind': 'object', 'signature': ''}, {'name': 'print_256', 'kind': 'object', 'signature': ''}, {'name': 'print_black', 'kind': 'object', 'signature': ''}, {'name': 'print_blue', 'kind': 'object', 'signature': ''}, {'name': 'print_cyan', 'kind': 'object', 'signature': ''}, {'name': 'print_green', 'kind': 'object', 'signature': ''}, {'name': 'print_magenta', 'kind': 'object', 'signature': ''}, {'name': 'print_red', 'kind': 'object', 'signature': ''}, {'name': 'print_rgb', 'kind': 'object', 'signature': ''}, {'name': 'print_white', 'kind': 'object', 'signature': ''}, {'name': 'print_yellow', 'kind': 'object', 'signature': ''}, {'name': 'reset_color_state', 'kind': 'object', 'signature': ''}, {'name': 'styled', 'kind': 'object', 'signature': ''}]
CONSTANTS = {}


def load_module():
    repo = Path(os.environ["RACB_REPO_ROOT"]).resolve()
    root = repo if MODULE_ROOT == "." else repo / MODULE_ROOT
    sys.path.insert(0, str(root))
    return importlib.import_module(MODULE)


def test_repeated_import_lookup_is_bounded():
    start = time.perf_counter()
    module = load_module()
    for _ in range(2000):
        for spec in SYMBOLS[:8]:
            getattr(module, spec["name"])
    assert time.perf_counter() - start < 10.0

