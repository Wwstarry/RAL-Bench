import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'chile_dtpm_gtfs'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'GTFSFeed', 'kind': 'object', 'signature': ''}, {'name': 'FeedMetadata', 'kind': 'object', 'signature': ''}, {'name': 'DTPM', 'kind': 'object', 'signature': ''}, {'name': 'FeedPublication', 'kind': 'object', 'signature': ''}]
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


def test_documented_nonpositive_download_limit_is_rejected():
    # docs/api.md, Errors: invalid configuration such as a nonpositive limit raises ValueError.
    from chile_dtpm_gtfs.source.downloader import FeedDownloader

    with pytest.raises(ValueError, match="max_bytes must be positive"):
        FeedDownloader(max_bytes=0)

