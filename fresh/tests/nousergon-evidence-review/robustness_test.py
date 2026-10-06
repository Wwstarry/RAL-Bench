import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'badges'
MODULE_ROOT = 'scripts'
SYMBOLS = [{'name': 'payloads', 'kind': 'function', 'signature': '(coverage, package)'}, {'name': 'main', 'kind': 'function', 'signature': '()'}]
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


def test_badges_refuse_unverified_or_missing_measurements():
    # README.md, "How do I verify it?" requires successful reproducible packaging.
    module = load_module()
    package = {"reproducible": False, "clean_install": True}
    with pytest.raises(ValueError, match="package verification incomplete"):
        module.payloads({"totals": {"num_statements": 1, "percent_covered": 100}}, package)
    package = {"reproducible": True, "clean_install": True}
    with pytest.raises(ValueError, match="coverage missing"):
        module.payloads({"totals": {"num_statements": 0, "percent_covered": 0}}, package)

