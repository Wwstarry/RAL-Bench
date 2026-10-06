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


def test_documented_seal_chain_and_canonical_jsonl():
    # README.md, "Transcript format" and "Sealing and the hash chain".
    from toolreplay.transcript import Record

    module = load_module()
    records = [
        Record(0, "read_file", {"path": "a.txt"}, {"text": "A"}),
        Record(1, "search", {"q": "x"}, {"hits": 2}),
    ]
    links = module.seal(records)
    assert links[0].prev == "0" * 64
    assert links[1].prev == links[0].digest
    assert module.verify(links).ok is True
    text = module.links_to_jsonl(links)
    assert text.endswith("\n")
    assert '"args":{"path":"a.txt"}' in text

