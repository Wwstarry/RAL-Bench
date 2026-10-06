import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'math_costs'
MODULE_ROOT = 'experiments'
SYMBOLS = [{'name': 'model_budget', 'kind': 'function', 'signature': '(name)'}, {'name': 'student_budget', 'kind': 'function', 'signature': '(name, n_student, d_student, i_student, h_student)'}, {'name': 'main', 'kind': 'function', 'signature': '()'}]
CONSTANTS = {'BANDWIDTH': 400000000000}


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


def test_student_budget_rejects_unknown_model():
    load_module()
    import math_costs
    with pytest.raises((FileNotFoundError, KeyError)):
        math_costs.student_budget("missing-checkpoint", 1, 16, 1, 1)


def test_unknown_model_and_zero_student_are_rejected(monkeypatch):
    mod = load_module()
    with pytest.raises(FileNotFoundError):
        mod.model_budget("not-a-model")
    monkeypatch.setattr(mod, "model_budget", lambda name: {"main_dense_weight_count": 1})
    with pytest.raises(ZeroDivisionError):
        mod.student_budget("laya", 0, 0, 0, 0)

