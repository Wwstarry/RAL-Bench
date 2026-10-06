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


def test_short_low_entropy_candidate_is_not_flagged_and_scan_is_stable():
    # README.md, "Entropy scoring": generic candidates need length, class mix and entropy.
    module = load_module()
    assert module.shannon_entropy("aaaa") == 0.0
    assert module.scan_line("token = abc") == []
    text = "Authorization: Bearer abcdefghijklmnopqrstuv"
    assert module.scan_line(text) == module.scan_line(text)

