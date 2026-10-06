import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'apex'
MODULE_ROOT = 'apex-py'
SYMBOLS = [{'name': 'Any', 'kind': 'object', 'signature': ''}, {'name': 'Dict', 'kind': 'object', 'signature': ''}, {'name': 'List', 'kind': 'object', 'signature': ''}, {'name': 'Optional', 'kind': 'object', 'signature': ''}, {'name': 'Union', 'kind': 'object', 'signature': ''}, {'name': 'DEFAULT_BLOCK_SIZE', 'kind': 'object', 'signature': ''}, {'name': 'FLAG_ENCRYPTED', 'kind': 'object', 'signature': ''}, {'name': 'FLAG_RECOVERY', 'kind': 'object', 'signature': ''}, {'name': 'ArchiveManifest', 'kind': 'object', 'signature': ''}, {'name': 'compress_archive', 'kind': 'object', 'signature': ''}, {'name': 'decompress_archive', 'kind': 'object', 'signature': ''}, {'name': 'read_archive_header', 'kind': 'object', 'signature': ''}, {'name': 'repair_archive', 'kind': 'object', 'signature': ''}, {'name': 'test_archive', 'kind': 'object', 'signature': ''}, {'name': 'analyze_file', 'kind': 'object', 'signature': ''}, {'name': 'run_benchmark', 'kind': 'object', 'signature': ''}]
CONSTANTS = {}


def load_module():
    repo = Path(os.environ["RACB_REPO_ROOT"]).resolve()
    root = repo if MODULE_ROOT == "." else repo / MODULE_ROOT
    sys.path.insert(0, str(root))
    return importlib.import_module(MODULE)


def test_public_surface_is_finite():
    module = load_module()
    names = dir(module)
    assert MODULE.split(".")[-1] in module.__name__
    assert len(names) < 10000

