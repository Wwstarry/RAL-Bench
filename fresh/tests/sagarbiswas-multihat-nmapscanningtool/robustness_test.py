import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'nmap_scanning_tool'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'entrypoint', 'kind': 'object', 'signature': ''}]
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


@pytest.mark.parametrize("target", ["", "bad host name", "-invalid.example"])
def test_invalid_targets_are_rejected(target):
    load_module()
    from nmap_scanning_tool.errors import ValidationError
    from nmap_scanning_tool.validation import validate_target
    with pytest.raises(ValidationError):
        validate_target(target)


@pytest.mark.parametrize("ports", ["0", "65536", "100-10", "22,,80"])
def test_invalid_ports_are_rejected(ports):
    load_module()
    from nmap_scanning_tool.errors import ValidationError
    from nmap_scanning_tool.validation import validate_ports
    with pytest.raises(ValidationError):
        validate_ports(ports)

