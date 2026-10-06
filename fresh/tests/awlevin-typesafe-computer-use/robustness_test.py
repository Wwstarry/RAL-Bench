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


def test_accessibility_zero_size_and_missing_frames_are_safe():
    module = load_module()
    assert module.off_display((0, 0, 0, 0), 1, 1) is False
    assert module.center_on_display(None, 1, 1) is True
    assert module.clickable(None) is False
    assert module.subtree_key("AXButton", "", None) is None


def test_missing_tiny_and_offscreen_frames_are_handled():
    mod = load_module()
    assert mod.clickable(None) is False
    assert mod.clickable((0, 0, 3, 20)) is False
    assert mod.center_on_display(None, 100, 100) is True
    assert mod.off_display((101, 0, 10, 10), 100, 100) is True

