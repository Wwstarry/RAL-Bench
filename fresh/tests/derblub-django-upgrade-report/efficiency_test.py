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


def test_repeated_import_lookup_is_bounded():
    start = time.perf_counter()
    module = load_module()
    for _ in range(2000):
        for spec in SYMBOLS[:8]:
            getattr(module, spec["name"])
    assert time.perf_counter() - start < 10.0

