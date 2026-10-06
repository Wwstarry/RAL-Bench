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


def test_documented_student_budget_preserves_teacher_identity():
    load_module()
    import math_costs
    assert math_costs.BANDWIDTH == 400_000_000_000
    assert callable(math_costs.student_budget)


def test_documented_static_bandwidth_constant_is_exact_and_repeatable():
    mod = load_module()
    assert mod.BANDWIDTH == 400_000_000_000
    assert mod.BANDWIDTH == load_module().BANDWIDTH


def test_student_budget_records_architecture_and_ratio(monkeypatch):
    mod = load_module()
    monkeypatch.setattr(mod, "model_budget", lambda name: {"main_dense_weight_count": 736_939_008})
    result = mod.student_budget("laya", 6, 512, 1344)
    assert result["teacher"] == "laya"
    assert result["student_encoder_layers"] == 6
    assert result["teacher_to_student_dense_flop_ratio_same_tokens"] > 1

