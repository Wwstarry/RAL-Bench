"""
Test DumpMaster functionality.
"""

import pytest
from mitmproxy.tools.dump import DumpMaster, DumpMasterOptions


def test_dump_master_creation():
    """Test creating a DumpMaster."""
    master = DumpMaster()
    assert master is not None
    assert master.running is False


def test_dump_master_with_options():
    """Test creating DumpMaster with options."""
    opts = DumpMasterOptions(
        listen_host="0.0.0.0",
        listen_port=9090,
        verbose=True
    )
    master = DumpMaster(opts)
    assert master.options.listen_host == "0.0.0.0"
    assert master.options.listen_port == 9090
    assert master.options.verbose is True


def test_dump_master_run():
    """Test running DumpMaster."""
    master = DumpMaster()
    master.run()
    assert master.running is False


def test_dump_master_shutdown():
    """Test shutting down DumpMaster."""
    master = DumpMaster()
    master.running = True
    master.shutdown()
    assert master.running is False