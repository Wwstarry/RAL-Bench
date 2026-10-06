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


def test_repeated_import_is_stable():
    first = load_module()
    assert importlib.import_module(MODULE) is first


def test_missing_public_name_raises_attribute_error():
    with pytest.raises(AttributeError):
        getattr(load_module(), "__ral_bench_missing_public_name__")


@pytest.mark.parametrize("spec", SYMBOLS)
def test_public_callables_are_introspectable(spec):
    value = getattr(load_module(), spec["name"])
    if spec["kind"] in {"function", "class"}:
        inspect.signature(value)


def test_documented_invalid_color_boundaries():
    termtint = load_module()
    with pytest.raises(ValueError):
        termtint.colored("x", "not-a-color")
    with pytest.raises(ValueError):
        termtint.colored("x", color="red", rgb=(1, 2, 3))
    with pytest.raises(ValueError):
        termtint.colored("x", color256=256)

