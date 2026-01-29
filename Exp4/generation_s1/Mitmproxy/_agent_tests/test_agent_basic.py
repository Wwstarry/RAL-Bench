import argparse

import pytest

from mitmproxy.addonmanager import AddonManager
from mitmproxy.flow import Flow
from mitmproxy.http import HTTPFlow, Headers, Request, Response
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.tools.main import mitmdump as main_mitmdump
import mitmproxy.tools.cmdline.mitmdump as cmd_mitmdump
from mitmproxy.version import __version__


def test_import_anchors():
    from mitmproxy.http import HTTPFlow as _
    from mitmproxy.flow import Flow as _
    from mitmproxy.addonmanager import AddonManager as _
    from mitmproxy.tools.dump import DumpMaster as _
    from mitmproxy.tools.main import mitmdump as _
    import mitmproxy.tools.cmdline.mitmdump as _


def test_cmdline_parse_defaults():
    ns = cmd_mitmdump.parse_args([])
    assert ns.listen_port == 8080
    assert ns.listen_host == "127.0.0.1"
    assert ns.mode == "regular"
    assert ns.quiet is False
    assert ns.verbose == 0
    assert ns.scripts == []
    assert ns.set == []
    assert ns.confdir == ""


def test_cmdline_parse_listen_port():
    ns = cmd_mitmdump.parse_args(["--listen-port", "8081"])
    assert ns.listen_port == 8081


def test_cmdline_help_contains_flags():
    p = argparse.ArgumentParser(prog="mitmdump", add_help=True)
    cmd_mitmdump.mitmdump(p)
    h = p.format_help()
    for token in ["--listen-port", "--listen-host", "--mode", "--set", "--version", "--confdir"]:
        assert token in h


def test_main_version_prints_and_exits(capsys):
    # argparse's --version exits with SystemExit(0)
    with pytest.raises(SystemExit) as ei:
        main_mitmdump(["--version"])
    assert ei.value.code == 0
    out = capsys.readouterr().out.strip()
    assert out == __version__


def test_master_lifecycle_runs_quickly():
    m = DumpMaster()
    assert m.should_exit is False
    m.run()
    assert m.should_exit is False
    m.shutdown()
    assert m.should_exit is True


def test_addon_hooks_order_and_remove():
    m = DumpMaster()
    calls = []

    class A:
        def running(self):
            calls.append("A.running")

        def done(self):
            calls.append("A.done")

    class B:
        def running(self):
            calls.append("B.running")

        def done(self):
            calls.append("B.done")

    a, b = A(), B()
    m.addons.add(a, b)
    m.run()
    assert calls == ["A.running", "B.running", "A.done", "B.done"]

    calls.clear()
    m.addons.remove(a)
    m.run()
    assert calls == ["B.running", "B.done"]


def test_http_headers_case_insensitive_and_multi():
    h = Headers([("X-Test", "1"), ("x-test", "2"), ("Other", "a")])
    assert h.get("x-test") == "2"
    assert h.get_all("X-TEST") == ["1", "2"]
    h["X-TEST"] = "3"
    assert h.get_all("x-test") == ["3"]


def test_httpflow_pretty_url_and_state_roundtrip():
    req = Request(host="example.com", port=8080, scheme="http", path="/hello", method="GET")
    req.headers["Host"] = "example.com"
    resp = Response(status_code=201, reason="Created", content=b"ok")
    f = HTTPFlow(request=req)
    f.response = resp
    assert f.request.pretty_url == "http://example.com:8080/hello"

    st = f.get_state()
    f2 = HTTPFlow()
    f2.set_state(st)
    assert f2.request is not None
    assert f2.response is not None
    assert f2.request.pretty_url == "http://example.com:8080/hello"
    assert f2.response.status_code == 201
    assert f2.response.content == b"ok"


def test_flow_kill_and_copy_metadata():
    f = Flow()
    f.metadata["a"] = {"b": 1}
    f2 = f.copy()
    assert f2 is not f
    assert f2.metadata == f.metadata
    f2.metadata["a"]["b"] = 2
    assert f.metadata["a"]["b"] == 1  # deep-copied metadata

    assert f.error is None
    f.kill()
    assert f.error is not None
    assert "killed" in str(f.error)