import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'dabook.config.loader'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'load_config', 'kind': 'function', 'signature': '(workspace_or_toml, overrides)'}, {'name': 'save_config', 'kind': 'function', 'signature': '(cfg, path)'}]
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


def test_invalid_profile_is_rejected_and_missing_config_is_deterministic(tmp_path):
    module = load_module()
    with pytest.raises(Exception):
        module.load_config(None, {"profile": "impossible"})
    first = module.load_config(tmp_path)
    second = module.load_config(tmp_path)
    assert first.model_dump() == second.model_dump()

