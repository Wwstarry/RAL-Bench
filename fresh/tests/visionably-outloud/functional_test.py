import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'outloud'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'annotations', 'kind': 'object', 'signature': ''}, {'name': 'Optional', 'kind': 'object', 'signature': ''}, {'name': 'Result', 'kind': 'object', 'signature': ''}, {'name': 'Document', 'kind': 'object', 'signature': ''}, {'name': 'features', 'kind': 'object', 'signature': ''}, {'name': 'load_catalogue', 'kind': 'object', 'signature': ''}, {'name': 'run_rules', 'kind': 'object', 'signature': ''}, {'name': 'check', 'kind': 'function', 'signature': '(path, source, only, skip, layers)'}]
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


def test_affine_helpers_and_missing_document_result(tmp_path):
    outloud = load_module()
    from outloud.content import apply, mul

    identity = (1, 0, 0, 1, 0, 0)
    translate = (1, 0, 0, 1, 5, -2)
    assert mul(identity, translate) == translate
    assert apply(translate, 3, 4) == (8, 2)
    result = outloud.check(tmp_path / "missing.pdf")
    assert result.findings == []
    assert result.error.startswith("FileNotFoundError:")

