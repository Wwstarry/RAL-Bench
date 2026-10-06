import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'hexmap_web'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'colour', 'kind': 'object', 'signature': ''}, {'name': 'fmt', 'kind': 'object', 'signature': ''}, {'name': 'geometry', 'kind': 'object', 'signature': ''}, {'name': 'hexbin', 'kind': 'object', 'signature': ''}, {'name': 'artifact_form', 'kind': 'object', 'signature': ''}, {'name': 'payload_2d', 'kind': 'object', 'signature': ''}, {'name': 'payload_3d', 'kind': 'object', 'signature': ''}, {'name': 'write_2d', 'kind': 'object', 'signature': ''}, {'name': 'write_3d', 'kind': 'object', 'signature': ''}, {'name': 'AreaLayer', 'kind': 'object', 'signature': ''}, {'name': 'Context', 'kind': 'object', 'signature': ''}, {'name': 'Field', 'kind': 'object', 'signature': ''}, {'name': 'MapSpec', 'kind': 'object', 'signature': ''}, {'name': 'Metric', 'kind': 'object', 'signature': ''}, {'name': 'Outline', 'kind': 'object', 'signature': ''}, {'name': 'Ranking', 'kind': 'object', 'signature': ''}]
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


def test_slice_key_is_deterministic_and_handles_no_slices():
    # README.md, "Toggles": unsliced quantities stay under their original key.
    module = load_module()
    assert module.slice_key("net") == "net"
    assert module.slice_key("net", "winter", "night") == module.slice_key("net", "winter", "night")

