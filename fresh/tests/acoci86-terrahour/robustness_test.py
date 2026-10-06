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


@pytest.mark.parametrize("text", ["in 0m", "25:99", "nonsense"])
def test_invalid_alert_text_returns_error_without_state_change(text):
    alerts = load_module()

    class State:
        alerts = []

    alert, error = alerts.parse_alert(text, State())
    assert alert is None
    assert error

