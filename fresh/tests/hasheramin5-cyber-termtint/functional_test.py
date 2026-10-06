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


def test_public_module_imports():
    assert load_module().__name__ == MODULE


@pytest.mark.parametrize("spec", SYMBOLS)
def test_declared_public_symbol(spec):
    value = getattr(load_module(), spec["name"])
    if spec["kind"] == "class":
        assert inspect.isclass(value)
    elif spec["kind"] == "function":
        assert callable(value)
    else:
        assert value is not None


@pytest.mark.parametrize("name, expected", list(CONSTANTS.items()))
def test_public_literal_constant(name, expected):
    assert getattr(load_module(), name) == expected


def test_documented_plain_text_and_color_state_transition():
    termtint = load_module()
    termtint.disable_color()
    assert termtint.styled("Plain text") == "Plain text"
    assert termtint.colored("Operation succeeded", "green") == "Operation succeeded"
    termtint.enable_color()
    assert termtint.colored("ok", "green") == "\x1b[32mok\x1b[0m"
    termtint.disable_color()
    assert termtint.colored("ok", "green") == "ok"

