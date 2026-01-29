"""
Test core API functionality.
"""

import pytest
from mitmproxy.http import HTTPFlow, HTTPRequest, HTTPResponse
from mitmproxy.flow import Flow, FlowType
from mitmproxy.addonmanager import AddonManager, Option


def test_http_flow_creation():
    """Test creating an HTTPFlow."""
    flow = HTTPFlow()
    assert flow.type == FlowType.HTTP
    assert flow.request is None
    assert flow.response is None


def test_http_request_creation():
    """Test creating an HTTPRequest."""
    req = HTTPRequest(
        method="POST",
        scheme="https",
        authority="example.com",
        path="/api/test"
    )
    assert req.method == "POST"
    assert req.scheme == "https"
    assert req.authority == "example.com"
    assert req.path == "/api/test"


def test_http_response_creation():
    """Test creating an HTTPResponse."""
    resp = HTTPResponse(
        status_code=404,
        reason="Not Found",
        content=b"Not found"
    )
    assert resp.status_code == 404
    assert resp.reason == "Not Found"
    assert resp.content == b"Not found"


def test_addon_manager_creation():
    """Test creating an AddonManager."""
    manager = AddonManager()
    assert len(manager.addons) == 0
    assert len(manager.options) == 0
    assert len(manager.commands) == 0


def test_addon_manager_add_option():
    """Test adding an option to AddonManager."""
    manager = AddonManager()
    manager.add_option("test_opt", str, "default_value", "Test option")
    assert "test_opt" in manager.options
    assert manager.options["test_opt"].default == "default_value"


def test_addon_manager_add_command():
    """Test adding a command to AddonManager."""
    manager = AddonManager()
    
    def test_cmd():
        return "executed"
    
    manager.add_command("test_cmd", test_cmd)
    assert "test_cmd" in manager.commands
    result = manager.trigger("test_cmd")
    assert result == "executed"


def test_flow_type_enum():
    """Test FlowType enumeration."""
    assert FlowType.HTTP.value == "http"
    assert FlowType.WEBSOCKET.value == "websocket"
    assert FlowType.TCP.value == "tcp"
    assert FlowType.UDP.value == "udp"