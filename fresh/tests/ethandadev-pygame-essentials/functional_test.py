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


def test_documented_label_text_and_position_state(monkeypatch):
    # README.md, "Positions and anchor" and "Label / Properties".
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    import pygame

    pygame.init()
    try:
        label = load_module().Label((10, 20), 42)
        assert label.text == "42"
        assert label.rect.topleft == (10, 20)
        label.text = "changed"
        assert label.text == "changed"
        assert label.rect.topleft == (10, 20)
    finally:
        pygame.quit()

