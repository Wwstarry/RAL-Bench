import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'hexmap_web'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'colour', 'kind': 'object', 'signature': ''}, {'name': 'fmt', 'kind': 'object', 'signature': ''}, {'name': 'geometry', 'kind': 'object', 'signature': ''}, {'name': 'hexbin', 'kind': 'object', 'signature': ''}, {'name': 'artifact_form', 'kind': 'object', 'signature': ''}, {'name': 'payload_2d', 'kind': 'object', 'signature': ''}, {'name': 'payload_3d', 'kind': 'object', 'signature': ''}, {'name': 'write_2d', 'kind': 'object', 'signature': ''}, {'name': 'write_3d', 'kind': 'object', 'signature': ''}, {'name': 'AreaLayer', 'kind': 'object', 'signature': ''}, {'name': 'Context', 'kind': 'object', 'signature': ''}, {'name': 'Field', 'kind': 'object', 'signature': ''}, {'name': 'MapSpec', 'kind': 'object', 'signature': ''}, {'name': 'Metric', 'kind': 'object', 'signature': ''}, {'name': 'Outline', 'kind': 'object', 'signature': ''}, {'name': 'Ranking', 'kind': 'object', 'signature': ''}]
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


def test_documented_toggle_slice_key_and_state():
    # README.md, "Toggles": exact key example and first option ordering.
    module = load_module()
    assert module.slice_key("net", "summer", "evening") == "net@summer@evening"
    toggle = module.Toggle("season", "Season", [("all", "All year"), ("summer", "Summer")])
    assert toggle.key == "season"
    assert toggle.options[0] == ("all", "All year")

