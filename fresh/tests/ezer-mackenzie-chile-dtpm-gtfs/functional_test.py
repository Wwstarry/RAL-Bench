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


def test_documented_publication_and_metadata_are_immutable_records():
    # docs/api.md, Discovery and Downloads: frozen publication and immutable metadata.
    from dataclasses import FrozenInstanceError
    from datetime import date

    module = load_module()
    publication = module.FeedPublication(
        "September feed", date(2026, 9, 1), "https://example.test/feed.zip", "feed.zip"
    )
    assert publication.effective_from == date(2026, 9, 1)
    assert publication.filename == "feed.zip"
    with pytest.raises(FrozenInstanceError):
        publication.title = "changed"

    metadata = module.FeedMetadata("a" * 64, "feed.zip", 123)
    assert (metadata.sha256, metadata.size_bytes, metadata.source_url) == ("a" * 64, 123, None)

