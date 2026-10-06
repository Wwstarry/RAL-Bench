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


def test_public_surface_is_finite():
    module = load_module()
    names = dir(module)
    assert MODULE.split(".")[-1] in module.__name__
    assert len(names) < 10000

