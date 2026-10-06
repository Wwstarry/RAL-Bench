import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'pynettcp'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'annotations', 'kind': 'object', 'signature': ''}, {'name': 'Channel', 'kind': 'object', 'signature': ''}, {'name': 'ChannelError', 'kind': 'object', 'signature': ''}, {'name': 'PyNetTcpError', 'kind': 'object', 'signature': ''}, {'name': 'FramingConnection', 'kind': 'object', 'signature': ''}, {'name': 'FramingError', 'kind': 'object', 'signature': ''}, {'name': 'FramingFault', 'kind': 'object', 'signature': ''}, {'name': 'connect', 'kind': 'object', 'signature': ''}, {'name': 'connect_secure', 'kind': 'object', 'signature': ''}, {'name': 'NegotiateStream', 'kind': 'object', 'signature': ''}, {'name': 'NnsError', 'kind': 'object', 'signature': ''}, {'name': 'SessionCodec', 'kind': 'object', 'signature': ''}, {'name': 'SessionDictionary', 'kind': 'object', 'signature': ''}, {'name': 'SessionSizeExceeded', 'kind': 'object', 'signature': ''}, {'name': 'BinaryXmlReader', 'kind': 'object', 'signature': ''}, {'name': 'BinaryXmlWriter', 'kind': 'object', 'signature': ''}]
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

