import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'toolreplay.chain'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'Link', 'kind': 'class', 'signature': 'class'}, {'name': 'seal', 'kind': 'function', 'signature': '(records)'}, {'name': 'VerifyResult', 'kind': 'class', 'signature': 'class'}, {'name': 'verify', 'kind': 'function', 'signature': '(links)'}, {'name': 'links_to_jsonl', 'kind': 'function', 'signature': '(links)'}, {'name': 'load_sealed', 'kind': 'function', 'signature': '(path)'}]
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


def test_documented_tamper_detection_reports_first_link():
    # README.md, "Sealing and the hash chain": changed response breaks at its index.
    from dataclasses import replace
    from toolreplay.transcript import Record

    module = load_module()
    links = module.seal([Record(0, "search", {"q": "x"}, {"hits": 3})])
    links[0] = replace(links[0], record=replace(links[0].record, response={"hits": 4}))
    result = module.verify(links)
    assert result.ok is False
    assert result.broken_index == 0
    assert result.expected != result.found

