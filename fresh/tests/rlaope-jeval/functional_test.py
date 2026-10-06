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


def test_documented_collection_loop_appends_decision_and_label(tmp_path):
    collect = importlib.import_module("jeval.collect")
    collect.reset_stats()
    records = tmp_path / "records.jsonl"
    assert collect.record(
        question_key="department", prediction="billing",
        probabilities={"billing": 0.82, "technical": 0.18}, model="jev-example",
        source_key="T-1042", path=records,
    ) is True
    assert collect.resolve(
        source_key="T-1042", question="department", answer="billing", path=records
    ) is True
    assert len(records.read_text(encoding="utf-8").splitlines()) == 1
    assert len((tmp_path / "labels.jsonl").read_text(encoding="utf-8").splitlines()) == 1
    assert collect.stats()["written"] == 1
    assert collect.stats()["labels_written"] == 1

