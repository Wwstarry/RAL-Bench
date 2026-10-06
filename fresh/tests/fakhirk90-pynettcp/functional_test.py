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


def test_documented_nbfx_envelope_bytes_are_exact_and_stable():
    module = load_module()
    soap12 = module.DictStr("http://www.w3.org/2003/05/soap-envelope")
    writer = module.BinaryXmlWriter()
    writer.start_element("s", module.DictStr("Envelope"), soap12)
    writer.start_element("s", module.DictStr("Body"), soap12)
    writer.end_element(); writer.end_element()
    assert writer.getvalue() == bytes.fromhex("56 02 0b 01 73 04 56 0e 01 01")
    assert writer.getvalue() == writer.getvalue()

