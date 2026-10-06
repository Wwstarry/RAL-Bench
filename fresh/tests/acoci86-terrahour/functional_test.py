import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'terrahour.alerts'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'resolve_place', 'kind': 'function', 'signature': '(st, name)'}, {'name': 'parse_alert', 'kind': 'function', 'signature': '(text, st)'}, {'name': 'alert_city', 'kind': 'function', 'signature': '(a)'}, {'name': 'notify', 'kind': 'function', 'signature': '(text)'}, {'name': 'check_alerts', 'kind': 'function', 'signature': '(st, live)'}]
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


def test_timer_alert_parse_and_one_shot_state_change(monkeypatch):
    alerts = load_module()

    class State:
        def __init__(self):
            self.alerts = []
            self.aidx = 0

    state = State()
    monkeypatch.setattr(alerts.time, "time", lambda: 1000.0)
    alert, error = alerts.parse_alert("in 2m", state)
    assert error == ""
    assert alert == {"kind": "timer", "name": "timer", "at": 1120.0}
    state.alerts = [alert]
    monkeypatch.setattr(alerts.time, "time", lambda: 1121.0)
    assert alerts.check_alerts(state, None) == ["Timer finished"]
    assert state.alerts == []

