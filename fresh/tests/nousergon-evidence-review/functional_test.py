import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'badges'
MODULE_ROOT = 'scripts'
SYMBOLS = [{'name': 'payloads', 'kind': 'function', 'signature': '(coverage, package)'}, {'name': 'main', 'kind': 'function', 'signature': '()'}]
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


def test_documented_measured_badge_payloads_are_exact():
    # README.md, badges and "How do I verify it?": badges follow successful measurements.
    result = load_module().payloads(
        {"totals": {"num_statements": 100, "percent_covered": 93.257}},
        {
            "reproducible": True,
            "clean_install": True,
            "source_sha": "abc123",
            "license": "MIT",
            "python": "3.12",
        },
    )
    assert result["coverage.json"] == {
        "schemaVersion": 1,
        "label": "Python coverage",
        "message": "93.26%",
        "color": "brightgreen",
        "sourceSha": "abc123",
    }
    assert result["license.json"]["message"] == "MIT"
    assert result["python.json"]["message"] == "3.12"

