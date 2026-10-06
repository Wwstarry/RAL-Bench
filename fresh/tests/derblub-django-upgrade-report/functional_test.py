import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'django_upgrade_report'
MODULE_ROOT = 'src'
SYMBOLS = []
CONSTANTS = {'COMPANY': 'Pushing Pixels', 'COMPANY_URL': 'https://pushingpixels.at', 'REPO_URL': 'https://github.com/derblub/django-upgrade-report'}


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


def test_poetry_alternative_version_constraints_are_parsed():
    load_module()
    from django_upgrade_report.analysis import spec_sets

    alternatives = spec_sets(">=4.2,<5 || >=5.1,<6")
    assert alternatives is not None and len(alternatives) == 2
    assert "4.2" in alternatives[0] and "5.0" not in alternatives[0]
    assert "5.2" in alternatives[1] and "6.0" not in alternatives[1]

