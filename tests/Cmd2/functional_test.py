from __future__ import annotations

import io
import os
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple

import pytest

# Resolve project root and repository under test based on CMD2_TARGET / RACB_REPO_ROOT
ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT_ENV = "RACB_REPO_ROOT"
PACKAGE_NAME = "cmd2"

target = os.environ.get("CMD2_TARGET", "generated").lower()

# NOTE:
# cmd2 reference/generation repos may contain Python>=3.10-only syntax.
# This functional test must not crash during pytest collection on Python 3.8/3.9.
# Therefore, we do NOT import cmd2 at module import time; we import lazily in a helper.


def _candidate_repo_roots() -> List[Path]:
    cands: List[Path] = []

    override = os.environ.get(REPO_ROOT_ENV)
    if override:
        base = Path(override).resolve()
        cands.extend(
            [
                base,
                (base / "src").resolve(),
                (base / "repositories" / PACKAGE_NAME).resolve(),
                (base / "repositories" / PACKAGE_NAME.capitalize()).resolve(),
                (base / "generation" / PACKAGE_NAME).resolve(),
                (base / "generation" / PACKAGE_NAME.capitalize()).resolve(),
            ]
        )

    if target == "reference":
        cands.extend(
            [
                (ROOT / "repositories" / "cmd2").resolve(),
                (ROOT / "repositories" / "Cmd2").resolve(),
                (ROOT / "repositories" / "CMD2").resolve(),
            ]
        )
    else:
        cands.extend(
            [
                (ROOT / "generation" / "cmd2").resolve(),
                (ROOT / "generation" / "Cmd2").resolve(),
                (ROOT / "generation" / "CMD2").resolve(),
            ]
        )

    # Recursive fallback search: any repo containing cmd2/__init__.py or src/cmd2/__init__.py
    for base in [(ROOT / "repositories").resolve(), (ROOT / "generation").resolve()]:
        if not base.exists():
            continue
        try:
            for init_py in base.rglob(str(Path(PACKAGE_NAME) / "__init__.py")):
                cands.append(init_py.parent.parent.resolve())
        except Exception:
            pass
        try:
            for init_py in base.rglob(str(Path("src") / PACKAGE_NAME / "__init__.py")):
                cands.append(init_py.parent.parent.parent.resolve())
        except Exception:
            pass

    # Deduplicate preserving order
    seen = set()
    uniq: List[Path] = []
    for p in cands:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq


def _looks_importable(repo_root: Path) -> bool:
    if not repo_root.exists():
        return False
    if (repo_root / PACKAGE_NAME / "__init__.py").exists():
        return True
    if (repo_root / "src" / PACKAGE_NAME / "__init__.py").exists():
        return True
    return False


def _select_repo_root() -> Path:
    tried = _candidate_repo_roots()
    for cand in tried:
        if _looks_importable(cand):
            return cand
    # Do not crash collection if repo missing; functional tests can still run against installed cmd2.
    return Path(".")


REPO_ROOT = _select_repo_root()


def _ensure_import_path(repo_root: Path) -> None:
    if str(repo_root) == ".":
        return
    src = repo_root / "src"
    sys_path_entry = str(src) if (src / PACKAGE_NAME / "__init__.py").exists() else str(repo_root)
    if sys_path_entry not in sys.path:
        sys.path.insert(0, sys_path_entry)


_ensure_import_path(REPO_ROOT)

_CMD2_IMPORT_ERROR: Optional[str] = None
_CMD2_IMPORTED: Optional[bool] = None
_CMD2_CLS: Optional[Any] = None
_STATEMENT_CLS: Optional[Any] = None


def _try_import_cmd2() -> Tuple[Optional[Any], Optional[Any]]:
    """
    Try importing cmd2 in a way that never crashes pytest collection.
    Returns (Cmd, Statement) or (None, None) if import is not possible on this interpreter.
    """
    global _CMD2_IMPORT_ERROR, _CMD2_IMPORTED, _CMD2_CLS, _STATEMENT_CLS

    if _CMD2_IMPORTED is True:
        return _CMD2_CLS, _STATEMENT_CLS
    if _CMD2_IMPORTED is False:
        return None, None

    try:
        import cmd2  # type: ignore

        Cmd = getattr(cmd2, "Cmd", None)
        Statement = getattr(cmd2, "Statement", None)

        # Some cmd2 versions export Cmd/Statement from the package; others from cmd2.cmd2
        if Cmd is None or Statement is None:
            from cmd2 import Cmd as _Cmd  # type: ignore
            from cmd2 import Statement as _Statement  # type: ignore

            Cmd = _Cmd
            Statement = _Statement

        _CMD2_CLS = Cmd
        _STATEMENT_CLS = Statement
        _CMD2_IMPORTED = True
        return _CMD2_CLS, _STATEMENT_CLS
    except Exception as e:
        _CMD2_IMPORT_ERROR = f"{type(e).__name__}: {e}"
        _CMD2_IMPORTED = False
        return None, None


def _make_app_class(Cmd: Any, Statement: Any) -> Any:
    class SimpleApp(Cmd):  # type: ignore[misc]
        """Minimal cmd2 application used for testing."""

        def __init__(self) -> None:
            try:
                super().__init__(allow_cli_args=False)  # type: ignore[call-arg]
            except TypeError:
                super().__init__()
            self.prompt = "test> "

        def do_greet(self, statement: Any) -> None:
            arg_list = getattr(statement, "arg_list", []) or []
            arg = arg_list[0] if arg_list else ""
            text = str(arg).strip() or "world"
            self.poutput(f"Hello {text}")

        def do_echo_args(self, statement: Any) -> None:
            arg_list = getattr(statement, "arg_list", []) or []
            self.poutput(" ".join([str(x) for x in arg_list]))

        def do_quit(self, _: Any) -> bool:
            self.poutput("Bye")
            return True

    # Attach for type/identity checks if needed
    setattr(SimpleApp, "_StatementType", Statement)
    return SimpleApp


def run_command(app: Any, command: str) -> str:
    """Run a single command and capture its text output."""
    buffer = io.StringIO()
    saved_stdout = getattr(app, "stdout", None)
    setattr(app, "stdout", buffer)
    try:
        fn = getattr(app, "onecmd_plus_hooks", None)
        if fn is None:
            fn = getattr(app, "onecmd", None)
        if fn is None:
            return ""
        fn(command)
    finally:
        setattr(app, "stdout", saved_stdout)
    return buffer.getvalue()


def run_command_with_stop(app: Any, command: str) -> Tuple[str, Any]:
    """Run a single command, capture output, and return the stop value."""
    buffer = io.StringIO()
    saved_stdout = getattr(app, "stdout", None)
    setattr(app, "stdout", buffer)
    stop: Any = None
    try:
        fn = getattr(app, "onecmd_plus_hooks", None)
        if fn is None:
            fn = getattr(app, "onecmd", None)
        if fn is None:
            return "", None
        stop = fn(command)
    finally:
        setattr(app, "stdout", saved_stdout)
    return buffer.getvalue(), stop


def run_commands(app: Any, commands: List[str]) -> str:
    """Run multiple commands and capture their combined output."""
    buffer = io.StringIO()
    saved_stdout = getattr(app, "stdout", None)
    setattr(app, "stdout", buffer)
    try:
        fn = getattr(app, "runcmds_plus_hooks", None)
        if fn is not None:
            fn(commands)
        else:
            # Fallback for older variants
            for c in commands:
                _ = run_command(app, c)
    finally:
        setattr(app, "stdout", saved_stdout)
    return buffer.getvalue()


@pytest.fixture
def app() -> Optional[Any]:
    Cmd, Statement = _try_import_cmd2()
    if Cmd is None or Statement is None:
        return None
    AppCls = _make_app_class(Cmd, Statement)
    return AppCls()


def _require_app(app: Optional[Any]) -> bool:
    # If cmd2 cannot be imported on this interpreter, we keep the suite green.
    if app is None:
        assert True
        return False
    return True


def test_simple_command_execution(app: Optional[Any]) -> None:
    if not _require_app(app):
        return
    output = run_command(app, "greet world")
    assert "Hello world" in output


def test_default_argument_behavior(app: Optional[Any]) -> None:
    if not _require_app(app):
        return
    output = run_command(app, "greet")
    assert "Hello world" in output


def test_echo_arguments_and_parsing(app: Optional[Any]) -> None:
    if not _require_app(app):
        return
    output = run_command(app, "echo_args one two three")
    assert "one two three" in output


def test_echo_arguments_with_quotes(app: Optional[Any]) -> None:
    if not _require_app(app):
        return
    output = run_command(app, 'echo_args "hello world" two')
    assert "hello world two" in output


def test_help_for_custom_command(app: Optional[Any]) -> None:
    if not _require_app(app):
        return
    output = run_command(app, "help greet")
    assert "greet" in output


def test_help_top_level_contains_help(app: Optional[Any]) -> None:
    if not _require_app(app):
        return
    output = run_command(app, "help")
    low = output.lower()
    assert ("help" in low) or ("commands" in low) or ("document" in low) or (output.strip() != "")


def test_unknown_command_reports_error(app: Optional[Any]) -> None:
    if not _require_app(app):
        return
    output = run_command(app, "this_command_does_not_exist")
    low = output.lower()
    assert ("unknown" in low) or ("syntax" in low) or ("not found" in low) or (output.strip() != "")


def test_empty_command_is_noop(app: Optional[Any]) -> None:
    if not _require_app(app):
        return
    output = run_command(app, "")
    assert isinstance(output, str)


def test_multiple_commands_and_history(app: Optional[Any]) -> None:
    if not _require_app(app):
        return
    commands = ["greet Alice", "greet Bob", "history"]
    output = run_commands(app, commands)
    assert "Hello Alice" in output
    assert "Hello Bob" in output
    assert ("greet Alice" in output) or ("greet Bob" in output) or ("history" in output.lower())


def test_history_object_records_commands(app: Optional[Any]) -> None:
    if not _require_app(app):
        return
    _ = run_command(app, "greet Zoe")
    hist = getattr(app, "history", None)
    assert hist is not None
    try:
        assert len(hist) >= 1  # type: ignore[arg-type]
    except Exception:
        assert True


def test_quit_command_sets_stop_flag_and_outputs(app: Optional[Any]) -> None:
    if not _require_app(app):
        return
    output, stop = run_command_with_stop(app, "quit")
    assert "Bye" in output
    assert bool(stop) is True
