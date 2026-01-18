import os
import re
import sys
import subprocess
from pathlib import Path


TARGET_ENV = "SQLMAP_TARGET"
TARGET_REFERENCE_VALUE = "reference"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _repo_root() -> Path:
    env_root = os.getenv("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return (_project_root() / "repositories" / "sqlmap").resolve()


def _entrypoint() -> Path:
    return (_repo_root() / "sqlmap.py").resolve()


def _run_cli(args, timeout_s=30) -> subprocess.CompletedProcess:
    """
    Non-invasive CLI execution only (help/version/invalid args).
    """
    cmd = [sys.executable, str(_entrypoint())] + list(args)
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_s,
        cwd=str(_repo_root()),
        env={**os.environ},
    )


def _out(p: subprocess.CompletedProcess) -> str:
    return (p.stdout + "\n" + p.stderr).lower()


def test_001_entrypoint_exists():
    assert _entrypoint().exists(), f"Missing sqlmap.py at: {_entrypoint()}"


def test_002_repo_contains_lib_directory():
    repo = _repo_root()
    assert (repo / "lib").exists(), f"Missing lib/ under repo root: {repo}"


def test_003_help_runs_and_mentions_usage_or_options():
    p = _run_cli(["-h"], timeout_s=30)
    assert p.returncode == 0
    out = _out(p)
    assert "usage" in out or "options" in out


def test_004_advanced_help_runs():
    p = _run_cli(["-hh"], timeout_s=30)
    assert p.returncode == 0
    out = _out(p)
    assert "target" in out or "request" in out or "enumeration" in out or "techniques" in out


def test_005_version_runs_and_prints_version_like_token():
    """
    sqlmap --version may print a raw version token (e.g. 1.9.12.3#dev) and may also
    print an 'exit' message. Do not require specific words like 'sqlmap'/'version'.
    """
    # --batch helps avoid interactive prompts on some builds, but keep tolerance regardless.
    p = _run_cli(["--batch", "--version"], timeout_s=30)
    out = _out(p)

    # Require a version-like token such as "1.9.12.3" optionally with suffix "#dev"
    assert re.search(r"\b\d+\.\d+(?:\.\d+){0,3}(?:#[a-z0-9]+)?\b", out) is not None


def test_006_invalid_option_reports_error_cleanly():
    """
    In sqlmap reference, invalid options can still return code 0 in some paths,
    but stderr includes 'no such option' (argparse style). We assert on the message.
    """
    p = _run_cli(["--this-option-should-not-exist"], timeout_s=30)
    out = _out(p)

    # Must clearly indicate option parsing failure; do NOT assert return code.
    assert ("no such option" in out) or ("unrecognized" in out) or ("unknown" in out)


def test_007_alignment_api_surface_symbols_importable():
    """
    Alignment anchors (must exist in BOTH reference and generated repos):

      - lib.parse.cmdline.cmdLineParser
      - lib.core.option.init, lib.core.option.initOptions
      - lib.core.data: cmdLineOptions, conf, kb
      - lib.core.settings: VERSION, DESCRIPTION
      - lib.controller.controller.start

    Only checks importability + symbol presence; does not execute scanning logic.
    """
    repo = _repo_root()
    sys.path.insert(0, str(repo))
    try:
        from lib.parse.cmdline import cmdLineParser  # noqa: F401
        from lib.core.option import init, initOptions  # noqa: F401
        from lib.core.data import cmdLineOptions, conf, kb  # noqa: F401
        from lib.core.settings import VERSION, DESCRIPTION  # noqa: F401
        from lib.controller.controller import start  # noqa: F401

        assert callable(cmdLineParser)
        assert callable(init)
        assert callable(initOptions)
        assert cmdLineOptions is not None
        assert conf is not None
        assert kb is not None
        assert isinstance(VERSION, str) and len(VERSION) > 0
        assert isinstance(DESCRIPTION, str) and len(DESCRIPTION) > 0
        assert callable(start)
    finally:
        if sys.path and sys.path[0] == str(repo):
            sys.path.pop(0)


def test_008_running_without_args_exits_or_prints_help():
    p = _run_cli([], timeout_s=30)
    out = (p.stdout + "\n" + p.stderr).strip()
    assert len(out) > 0


def test_009_unicode_output_dir_argument_stable_in_help_mode():
    root = _project_root()
    out_dir = root / "generation" / "Sqlmap" / "tmp_输出"
    out_dir.mkdir(parents=True, exist_ok=True)

    p = _run_cli(["-h", "--output-dir", str(out_dir)], timeout_s=30)
    assert p.returncode == 0
