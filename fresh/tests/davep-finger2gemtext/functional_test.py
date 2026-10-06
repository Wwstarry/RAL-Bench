import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'finger2gemtext'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'version', 'kind': 'object', 'signature': ''}, {'name': 'AvailableServicesFilter', 'kind': 'object', 'signature': ''}, {'name': 'finger_to_gemtext', 'kind': 'object', 'signature': ''}, {'name': 'FingerFilter', 'kind': 'object', 'signature': ''}, {'name': 'UserListFilter', 'kind': 'object', 'signature': ''}]
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


def test_documented_converter_maps_string_to_exact_gemtext_string():
    # README.md, "Quick start": one string input produces one Gemtext string.
    convert = load_module().finger_to_gemtext
    assert convert("A plain finger response") == "A plain finger response"
    assert convert("") == ""

