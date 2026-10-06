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


def test_documented_empty_and_boundary_ranges():
    module = load_module()
    assert list(module.ranges.empty()) == []
    assert list(module.ranges.iota(5, 5)) == []
    assert ("abcdef" | module.views.take(0) | module.views.to(str)) == ""
    with pytest.raises(TypeError):
        42 | module.views.all()

