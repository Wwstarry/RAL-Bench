"""
Test that all required modules can be imported.
"""

import pytest


def test_import_http():
    """Test importing mitmproxy.http module."""
    from mitmproxy import http
    assert hasattr(http, 'HTTPFlow')
    assert hasattr(http, 'HTTPRequest')
    assert hasattr(http, 'HTTPResponse')


def test_import_flow():
    """Test importing mitmproxy.flow module."""
    from mitmproxy import flow
    assert hasattr(flow, 'Flow')
    assert hasattr(flow, 'Request')
    assert hasattr(flow, 'Response')


def test_import_addonmanager():
    """Test importing mitmproxy.addonmanager module."""
    from mitmproxy import addonmanager
    assert hasattr(addonmanager, 'AddonManager')
    assert hasattr(addonmanager, 'Option')


def test_import_tools_main():
    """Test importing mitmproxy.tools.main module."""
    from mitmproxy.tools import main
    assert hasattr(main, 'mitmdump')


def test_import_tools_dump():
    """Test importing mitmproxy.tools.dump module."""
    from mitmproxy.tools import dump
    assert hasattr(dump, 'DumpMaster')


def test_import_tools_cmdline():
    """Test importing mitmproxy.tools.cmdline module."""
    from mitmproxy.tools import cmdline
    assert hasattr(cmdline, 'mitmdump')


def test_import_tools_mitmweb():
    """Test importing mitmproxy.tools.mitmweb module."""
    from mitmproxy.tools import mitmweb
    assert hasattr(mitmweb, 'MitmwebMaster')


def test_import_tools_console():
    """Test importing mitmproxy.tools.console module."""
    from mitmproxy.tools import console
    assert hasattr(console, 'ConsoleMaster')


def test_import_addons_core():
    """Test importing mitmproxy.addons.core module."""
    from mitmproxy.addons import core
    assert hasattr(core, 'Core')


def test_import_addons_proxyserver():
    """Test importing mitmproxy.addons.proxyserver module."""
    from mitmproxy.addons import proxyserver
    assert hasattr(proxyserver, 'Proxyserver')


def test_import_addons_eventstore():
    """Test importing mitmproxy.addons.eventstore module."""
    from mitmproxy.addons import eventstore
    assert hasattr(eventstore, 'EventStore')