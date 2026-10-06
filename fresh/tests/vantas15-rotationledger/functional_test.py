import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'rotationledger'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'annotations', 'kind': 'object', 'signature': ''}, {'name': 'Finding', 'kind': 'object', 'signature': ''}, {'name': 'scan_line', 'kind': 'object', 'signature': ''}, {'name': 'CharClasses', 'kind': 'object', 'signature': ''}, {'name': 'classify', 'kind': 'object', 'signature': ''}, {'name': 'looks_random', 'kind': 'object', 'signature': ''}, {'name': 'shannon_entropy', 'kind': 'object', 'signature': ''}, {'name': 'Lifetime', 'kind': 'object', 'signature': ''}, {'name': 'reconstruct', 'kind': 'object', 'signature': ''}, {'name': 'Commit', 'kind': 'object', 'signature': ''}, {'name': 'DiffLine', 'kind': 'object', 'signature': ''}, {'name': 'parse_log', 'kind': 'object', 'signature': ''}]
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


def test_documented_structural_secret_rules_and_fingerprints():
    # README.md, "Detection rules" and "Why fingerprints and not values".
    module = load_module()
    bearer = module.scan_line("Authorization: Bearer abcdefghijklmnopqrstuv")
    aws = module.scan_line("AKIA1234567890ABCDEF")
    assert [item.rule for item in bearer] == ["bearer-token"]
    assert [item.rule for item in aws] == ["aws-access-key"]
    assert len(bearer[0].fingerprint) == 12
    assert "abcdefghijklmnopqrstuv" not in repr(bearer[0])

