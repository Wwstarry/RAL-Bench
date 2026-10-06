import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'atm'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'IndexStats', 'kind': 'object', 'signature': ''}, {'name': 'SessionEntry', 'kind': 'object', 'signature': ''}, {'name': 'SessionIndex', 'kind': 'object', 'signature': ''}, {'name': 'Source', 'kind': 'object', 'signature': ''}]
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


def test_memory_size_normalization_and_conversion():
    load_module()
    from atm.config import size_to_bytes, validate_size

    assert validate_size("MemoryHigh", " 4g ") == "4G"
    assert size_to_bytes("4G") == 4 * 1024 ** 3
    assert size_to_bytes("512M") == 512 * 1024 ** 2
    assert size_to_bytes("infinity") is None

