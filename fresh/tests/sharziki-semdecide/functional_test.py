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


def test_documented_guard_decision_routes_authorized_low_risk_and_secrets():
    module = load_module()
    base = {k: {"noul": 0.0} for k in ("destructive", "external_side_effect", "secret_exposure", "authorized", "intent_clear")}
    base["consequence"] = {"score": 0.1}
    base["authorized"]["noul"] = 1.0
    assert module.decide(base).route == "allow"
    base["secret_exposure"]["noul"] = 0.9
    assert module.decide(base).route == "block"


def _answers(**overrides):
    values = {
        "destructive": {"noul": 0.0}, "external_side_effect": {"noul": 0.0},
        "secret_exposure": {"noul": 0.0}, "authorized": {"noul": 1.0},
        "intent_clear": {"noul": 1.0}, "consequence": {"score": 0.1},
        "advisory_route": {"choice": "allow", "confidence": 0.9},
    }
    values.update(overrides)
    return values


def test_documented_guard_policy_routes_exactly_and_repeatably():
    mod = load_module()
    allowed = mod.decide(_answers(), model="jev-example", latency_ms=12)
    assert (allowed.route, allowed.reason, allowed.model, allowed.latency_ms) == (
        "allow", "explicitly authorized low-risk action", "jev-example", 12)
    assert mod.decide(_answers()).route == mod.decide(_answers()).route == "allow"
    blocked = mod.decide(_answers(secret_exposure={"noul": 0.9}))
    assert blocked.route == "block"

