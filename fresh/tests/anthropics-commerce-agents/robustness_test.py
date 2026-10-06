import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'commerce_common.config'
MODULE_ROOT = 'commerce-common'
SYMBOLS = [{'name': 'BaseAgentConfig', 'kind': 'class', 'signature': 'class'}]
CONSTANTS = {'DEFAULT_MEMORY_MODEL': 'claude-haiku-4-5-20251001'}


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


def test_config_enforces_documented_bounds_and_required_model():
    cls = load_module().BaseAgentConfig
    with pytest.raises(Exception):
        cls()
    with pytest.raises(Exception):
        cls(model="x", max_search_results=26)
    with pytest.raises(Exception):
        cls(model="x", memory_retention_days=0)

