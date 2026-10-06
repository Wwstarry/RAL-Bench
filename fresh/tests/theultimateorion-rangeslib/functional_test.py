import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'rangeslib'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'ranges', 'kind': 'object', 'signature': ''}, {'name': 'views', 'kind': 'object', 'signature': ''}, {'name': 'Range', 'kind': 'object', 'signature': ''}]
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


def test_documented_pipeline_and_reuse_examples():
    module = load_module()
    pipeline = module.views.filter(lambda value: value % 2 == 0) | module.views.take(3)
    assert list([1, 2, 3, 4, 5, 6] | pipeline) == [2, 4, 6]
    assert list([10, 11, 12, 14] | pipeline) == [10, 12, 14]
    result = (module.ranges.iota(1, 11) | module.views.filter(lambda x: x % 2 == 0)
              | module.views.transform(lambda x: x * 10) | module.views.take(3)
              | module.views.to(list))
    assert result == [20, 40, 60]

