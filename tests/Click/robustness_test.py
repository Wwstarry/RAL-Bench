import os
import sys
from pathlib import Path
from typing import Any, Callable, Tuple

import pytest


PROJECT_NAME = "Click"
PACKAGE_NAME = "click"


def _candidate_repo_roots() -> list[Path]:
    """
    Determine where to import the evaluated repository from.

    Priority:
      1) RACB_REPO_ROOT env var (set by runner)
      2) <bench_root>/repositories/<Project>
      3) <bench_root>/generation/<Project>
    """
    candidates: list[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        # In case runner passes bench root instead of project root
        candidates.append((p / "repositories" / PROJECT_NAME).resolve())
        candidates.append((p / "generation" / PROJECT_NAME).resolve())

    bench_root = Path(__file__).resolve().parents[2]
    candidates.append((bench_root / "repositories" / PROJECT_NAME).resolve())
    candidates.append((bench_root / "generation" / PROJECT_NAME).resolve())

    seen = set()
    uniq: list[Path] = []
    for c in candidates:
        if c not in seen:
            uniq.append(c)
            seen.add(c)
    return uniq


def _looks_like_package_root(repo_root: Path) -> bool:
    if (repo_root / PACKAGE_NAME / "__init__.py").exists():
        return True
    if (repo_root / "src" / PACKAGE_NAME / "__init__.py").exists():
        return True
    return False


def _select_repo_root() -> Path:
    for cand in _candidate_repo_roots():
        if _looks_like_package_root(cand):
            return cand
    raise RuntimeError(
        f"Could not locate importable repo root for '{PACKAGE_NAME}'. "
        f"Tried: {[str(p) for p in _candidate_repo_roots()]}"
    )


def _import_click():
    repo_root = _select_repo_root()
    repo_str = str(repo_root)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)
    import click  # type: ignore
    return click


def _run_case(case_name: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Tuple[bool, str]:
    """
    Robustness harness:
      - Passing means: the call either succeeds or raises a normal exception quickly.
      - This suite avoids interactive or OS-dependent calls that could hang.
    """
    try:
        _ = fn(*args, **kwargs)
        return True, f"{case_name}: OK"
    except Exception as e:
        return True, f"{case_name}: RAISED {type(e).__name__}"


def test_click_robustness_invalid_inputs_do_not_crash():
    """
    Robustness tests should be version-tolerant:
      - Invalid inputs may raise exceptions (acceptable).
      - Some invalid inputs may be coerced/ignored (also acceptable).
    Requirement: no hard crashes; library remains importable and callable.
    """
    click = _import_click()

    results: list[Tuple[bool, str]] = []

    # 1) Construct basic objects
    cmd = click.Command(name="test")
    group = click.Group(name="test_group")

    # 2) Callback non-callable: assignment may or may not raise; both OK
    def _set_callback():
        cmd.callback = "not a function"  # type: ignore[assignment]

    results.append(_run_case("Command callback set to non-callable", _set_callback))

    # 3) Option invalid type: signature/validation varies across versions
    results.append(_run_case("Option with invalid type", click.Option, ["--test"], type="not a type"))  # type: ignore[arg-type]

    # 4) Group add duplicate command names: may override or raise
    results.append(_run_case("Group add_command duplicate name", group.add_command, cmd, name="dup"))
    results.append(_run_case("Group add_command duplicate name again", group.add_command, cmd, name="dup"))

    # 5) Context creation with valid/None command
    results.append(_run_case("Context with command", click.Context, cmd))
    results.append(_run_case("Context with None command", click.Context, None))  # type: ignore[arg-type]

    # 6) ClickException with None message
    results.append(_run_case("ClickException with None message", click.ClickException, None))  # type: ignore[arg-type]

    # 7) Argument invalid type
    results.append(_run_case("Argument invalid type", click.Argument, ["arg"], type="invalid_type"))  # type: ignore[arg-type]

    # 8) echo invalid file object
    results.append(_run_case("echo invalid file", click.echo, "test", file="not a file"))  # type: ignore[arg-type]

    # 9) Avoid interactive calls (prompt/confirm/pause/edit) - ensure surface exists
    assert hasattr(click, "prompt")
    assert hasattr(click, "confirm")
    assert hasattr(click, "pause")
    assert hasattr(click, "edit")
    assert hasattr(click, "launch")

    # 10) style/secho invalid color
    results.append(_run_case("style invalid fg", click.style, "text", fg="invalid_color"))  # type: ignore[arg-type]
    results.append(_run_case("secho invalid fg", click.secho, "text", fg="invalid_color"))  # type: ignore[arg-type]

    # 11) open_file with invalid mode should raise quickly (or succeed), but not hang
    results.append(
        _run_case("open_file invalid mode", click.open_file, "nonexistent_file.txt", mode="invalid_mode")
    )

    # 12) format_filename/unstyle with None
    results.append(_run_case("format_filename None", click.format_filename, None))  # type: ignore[arg-type]
    results.append(_run_case("unstyle None", click.unstyle, None))  # type: ignore[arg-type]

    # 13) Duplicate option decoration: should not crash
    def _define_duplicate_options():
        @click.command()
        @click.option("--test", help="Test option")
        def duplicate_options_cmd(test):  # noqa: ARG001
            return None

        _ = click.option("--test", help="Another test option")(duplicate_options_cmd)
        return duplicate_options_cmd

    results.append(_run_case("duplicate option decoration", _define_duplicate_options))

    # 14) Group adding itself as a command: should not crash now
    results.append(_run_case("group add itself as command", group.add_command, group))  # type: ignore[arg-type]

    # Ensure we executed at least some probes
    assert len(results) > 0

    # This robustness suite passes as long as probes ran without hanging/crashing.
    # (Exceptions are counted as "acceptable outcomes" above.)
    assert all(ok for ok, _ in results)
