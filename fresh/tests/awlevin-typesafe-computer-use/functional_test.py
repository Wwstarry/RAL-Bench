import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'typesafe_computer_use.ax_walk'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'AxAttrs', 'kind': 'class', 'signature': 'class'}, {'name': 'off_display', 'kind': 'function', 'signature': '(frame, display_w_pt, display_h_pt)'}, {'name': 'center_on_display', 'kind': 'function', 'signature': '(frame, display_w_pt, display_h_pt)'}, {'name': 'node_identity', 'kind': 'function', 'signature': '(node)'}, {'name': 'subtree_key', 'kind': 'function', 'signature': '(role, label, frame)'}, {'name': 'clickable', 'kind': 'function', 'signature': '(frame)'}, {'name': 'descendant_label', 'kind': 'function', 'signature': '(kids, children, attrs)'}, {'name': 'walk_actionable', 'kind': 'function', 'signature': '(root, children, attrs, actions, display_w_pt, display_h_pt, node_cap, time_cap, offscreen_cap, clock)'}]
CONSTANTS = {'AX_PRESS': 'AXPress', 'AX_NODE_CAP': 4000, 'AX_TIME_CAP': 0.6, 'AX_OFFSCREEN_CAP': 120, 'AX_MIN_SIDE_PT': 4.0, 'AX_FANOUT': 8}


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


def test_accessibility_geometry_rules_are_deterministic():
    module = load_module()
    assert module.off_display((100, 0, 10, 10), 100, 100) is True
    assert module.center_on_display((0, 0, 10, 10), 100, 100) is True
    assert module.clickable((0, 0, 4, 4)) is True
    assert module.subtree_key("AXButton", "Save", (1.2, 2.7, 40, 20)) == ("AXButton", "Save", 1, 3, 40, 20)


def test_documented_accessibility_geometry_classification_is_repeatable():
    mod = load_module()
    frame = (10.0, 20.0, 40.0, 20.0)
    assert mod.center_on_display(frame, 100, 100) is True
    assert mod.off_display(frame, 100, 100) is False
    assert mod.clickable(frame) is True
    assert mod.subtree_key("AXButton", "Save", frame) == mod.subtree_key("AXButton", "Save", frame)

