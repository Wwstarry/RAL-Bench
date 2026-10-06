import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'macos'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'appearance', 'kind': 'object', 'signature': ''}, {'name': 'apps', 'kind': 'object', 'signature': ''}, {'name': 'audio', 'kind': 'object', 'signature': ''}, {'name': 'auth', 'kind': 'object', 'signature': ''}, {'name': 'bluetooth', 'kind': 'object', 'signature': ''}, {'name': 'browser', 'kind': 'object', 'signature': ''}, {'name': 'camera', 'kind': 'object', 'signature': ''}, {'name': 'clipboard', 'kind': 'object', 'signature': ''}, {'name': 'defaults', 'kind': 'object', 'signature': ''}, {'name': 'dialog', 'kind': 'object', 'signature': ''}, {'name': 'dock', 'kind': 'object', 'signature': ''}, {'name': 'document', 'kind': 'object', 'signature': ''}, {'name': 'events', 'kind': 'object', 'signature': ''}, {'name': 'finder', 'kind': 'object', 'signature': ''}, {'name': 'hotkeys', 'kind': 'object', 'signature': ''}, {'name': 'image', 'kind': 'object', 'signature': ''}]
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


def test_documented_image_info_value_object_is_stable():
    image = load_module().image
    info = image.ImageInfo(4032, 3024, "heic", False, 1, 72.0)
    assert (info.width, info.height, info.format) == (4032, 3024, "heic")
    assert info == image.ImageInfo(4032, 3024, "heic", False, 1, 72.0)
    assert hash(info) == hash(image.ImageInfo(4032, 3024, "heic", False, 1, 72.0))

