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


def test_documented_target_port_and_argument_validation():
    load_module()
    from nmap_scanning_tool.validation import validate_custom_args, validate_ports, validate_target

    assert validate_target(" 192.168.1.1 ") == "192.168.1.1"
    assert validate_target("scan.example.com") == "scan.example.com"
    assert validate_ports(" 22,80,443,8000-8100 ") == "22,80,443,8000-8100"
    assert validate_custom_args([" -sV ", "", "--script=vuln"]) == ("-sV", "--script=vuln")

