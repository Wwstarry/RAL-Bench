import os
import sys
import subprocess
import re

import pytest


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def run_cli(args):
    proc = subprocess.run(
        [sys.executable, os.path.join(REPO_ROOT, "sqlmap.py"), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=10,
    )
    return proc


def test_import_surface():
    from lib.parse.cmdline import cmdLineParser  # noqa: F401
    from lib.core.option import init, initOptions  # noqa: F401
    from lib.core.data import cmdLineOptions, conf, kb  # noqa: F401
    from lib.core.settings import VERSION, DESCRIPTION  # noqa: F401
    from lib.controller.controller import start  # noqa: F401


def test_help_basic():
    p = run_cli(["-h"])
    assert p.returncode == 0
    assert "usage:" in p.stdout.lower()
    assert "--version" in p.stdout


def test_help_advanced_hh():
    p = run_cli(["-hh"])
    assert p.returncode == 0
    assert "advanced help" in p.stdout.lower()
    assert "-u, --url" in p.stdout


def test_version():
    from lib.core.settings import VERSION
    p = run_cli(["--version"])
    assert p.returncode == 0
    out = p.stdout.strip()
    assert out == f"sqlmap/{VERSION}"


def test_invalid_argument_exits_cleanly():
    p = run_cli(["--does-not-exist"])
    assert p.returncode == 2
    assert "unrecognized arguments" in p.stderr.lower()
    assert "traceback" not in (p.stderr.lower() + p.stdout.lower())


def test_missing_value_exits_cleanly():
    p = run_cli(["-u"])
    assert p.returncode == 2
    assert "expected one argument" in p.stderr.lower()
    assert "traceback" not in (p.stderr.lower() + p.stdout.lower())


def test_no_args_prints_help():
    p = run_cli([])
    assert p.returncode == 0
    assert "usage:" in p.stdout.lower()


def test_batch_only_exits_cleanly_with_hint():
    p = run_cli(["--batch"])
    assert p.returncode == 0
    assert "no target provided" in p.stderr.lower()
    assert "traceback" not in (p.stderr.lower() + p.stdout.lower())


def test_state_initialization_sets_conf_url():
    from lib.core.option import initOptions
    from lib.parse.cmdline import cmdLineParser
    from lib.core.data import conf

    opts = cmdLineParser(["-u", "http://example.com/?id=1", "--batch", "-v", "2"])
    initOptions(opts)
    assert conf.url == "http://example.com/?id=1"
    assert conf.batch is True
    assert conf.verbose == 2