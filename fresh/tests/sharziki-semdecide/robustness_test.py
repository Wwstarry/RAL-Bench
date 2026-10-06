import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'reflex_guard'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'Decision', 'kind': 'object', 'signature': ''}, {'name': 'decide', 'kind': 'object', 'signature': ''}]
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


def test_decision_missing_signal_fails_closed():
    module = load_module()
    with pytest.raises(KeyError):
        module.decide({})


def test_guard_policy_escalates_ambiguous_and_rejects_missing_signals():
    mod = load_module()
    answers = {
        "destructive": {"noul": 0.0}, "external_side_effect": {"noul": 0.0},
        "secret_exposure": {"noul": 0.0}, "authorized": {"noul": 1.0},
        "intent_clear": {"noul": 0.2}, "consequence": {"score": 0.7},
    }
    assert mod.decide(answers).route == "escalate"
    with pytest.raises(KeyError):
        mod.decide({})

