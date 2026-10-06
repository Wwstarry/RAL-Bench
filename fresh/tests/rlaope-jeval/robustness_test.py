import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'jeval'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'annotations', 'kind': 'object', 'signature': ''}, {'name': 'PackageNotFoundError', 'kind': 'object', 'signature': ''}, {'name': 'version', 'kind': 'object', 'signature': ''}]
CONSTANTS = {'DISTRIBUTION': 'jeval-cli'}


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


def test_collection_off_switch_is_repeatable_and_invalid_values_are_dropped(tmp_path, monkeypatch):
    collect = importlib.import_module("jeval.collect")
    collect.reset_stats()
    path = tmp_path / "records.jsonl"
    monkeypatch.setenv("JEVAL_COLLECT", "0")
    kwargs = dict(question_key="q", prediction="yes", probabilities={"yes": 1.0}, path=path)
    assert collect.record(**kwargs) is False
    assert collect.record(**kwargs) is False
    assert not path.exists()
    monkeypatch.delenv("JEVAL_COLLECT")
    assert collect.record(question_key="", prediction="yes", path=path) is False
    assert collect.stats()["dropped"] >= 1

