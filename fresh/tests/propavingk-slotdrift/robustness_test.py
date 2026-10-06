import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'slotdrift.cli'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'build_parser', 'kind': 'function', 'signature': '()'}, {'name': 'load', 'kind': 'function', 'signature': '(path)'}, {'name': 'main', 'kind': 'function', 'signature': '(argv)'}]
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


def test_cli_missing_input_has_documented_usage_exit(tmp_path):
    module = load_module()
    with pytest.raises(SystemExit) as exc:
        module.load(tmp_path / "missing.jsonl")
    assert exc.value.code == 2

