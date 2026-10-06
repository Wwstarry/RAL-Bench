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


def test_converter_is_deterministic_and_rejects_non_string_input():
    # README.md, "Quick start" declares a string input and string output.
    convert = load_module().finger_to_gemtext
    value = "Available fingers:\nuser: description"
    assert convert(value) == convert(value)
    with pytest.raises((TypeError, AttributeError)):
        convert(None)

