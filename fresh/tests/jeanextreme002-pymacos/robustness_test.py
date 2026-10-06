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


def test_documented_image_info_is_immutable_and_constructor_is_strict():
    from dataclasses import FrozenInstanceError
    image = load_module().image
    info = image.ImageInfo(1, 1, "png", True, 1, None)
    with pytest.raises(FrozenInstanceError):
        info.width = 2
    with pytest.raises(TypeError):
        image.ImageInfo(1, 1)

