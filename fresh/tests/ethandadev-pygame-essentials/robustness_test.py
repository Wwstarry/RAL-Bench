import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'pygame_essentials'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'check_pygame', 'kind': 'object', 'signature': ''}, {'name': 'Button', 'kind': 'object', 'signature': ''}, {'name': 'Checkbox', 'kind': 'object', 'signature': ''}, {'name': 'Dropdown', 'kind': 'object', 'signature': ''}, {'name': 'Label', 'kind': 'object', 'signature': ''}, {'name': 'ProgressBar', 'kind': 'object', 'signature': ''}, {'name': 'Slider', 'kind': 'object', 'signature': ''}, {'name': 'TextInput', 'kind': 'object', 'signature': ''}, {'name': 'Toggle', 'kind': 'object', 'signature': ''}, {'name': 'Widget', 'kind': 'object', 'signature': ''}, {'name': 'resolve_font', 'kind': 'object', 'signature': ''}, {'name': 'Animation', 'kind': 'object', 'signature': ''}, {'name': 'AnimationSet', 'kind': 'object', 'signature': ''}, {'name': 'Spritesheet', 'kind': 'object', 'signature': ''}, {'name': 'Camera', 'kind': 'object', 'signature': ''}, {'name': 'DebugOverlay', 'kind': 'object', 'signature': ''}]
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


def test_documented_anchor_rejects_unknown_value(monkeypatch):
    # README.md, "Positions and anchor" enumerates the accepted anchors.
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    import pygame

    pygame.init()
    try:
        with pytest.raises(ValueError, match="anchor must be one of"):
            load_module().Label((0, 0), "x", anchor="outside")
    finally:
        pygame.quit()

