from __future__ import annotations

import io
import os
import sys
from pathlib import Path
from typing import Tuple

import pytest

# ---------------------------------------------------------------------------
# Repo root resolution (RACB-compatible + local fallback)
# ---------------------------------------------------------------------------

PACKAGE_NAME = "rich"

_racb_root = os.environ.get("RACB_REPO_ROOT", "").strip()
if _racb_root:
    REPO_ROOT = Path(_racb_root).resolve()
else:
    ROOT = Path(__file__).resolve().parents[2]
    target = os.environ.get("RICH_TARGET", "generated").lower()
    if target == "reference":
        REPO_ROOT = ROOT / "repositories" / "rich"
    elif target == "generated":
        REPO_ROOT = ROOT / "generation" / "Rich"
    else:
        pytest.skip("Unknown RICH_TARGET={!r}".format(target), allow_module_level=True)

if not REPO_ROOT.exists():
    pytest.skip("Repository root does not exist: {}".format(REPO_ROOT), allow_module_level=True)

src_pkg_init = REPO_ROOT / "src" / PACKAGE_NAME / "__init__.py"
root_pkg_init = REPO_ROOT / PACKAGE_NAME / "__init__.py"

if src_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT))
else:
    pytest.skip(
        "Could not find '{}' package under repo root. Expected {} or {}.".format(
            PACKAGE_NAME, src_pkg_init, root_pkg_init
        ),
        allow_module_level=True,
    )

try:
    from rich.console import Console  # type: ignore  # noqa: E402
    from rich.table import Table  # type: ignore  # noqa: E402
    from rich.progress import Progress  # type: ignore  # noqa: E402
    from rich.text import Text  # type: ignore  # noqa: E402
    from rich.panel import Panel  # type: ignore  # noqa: E402
    from rich.columns import Columns  # type: ignore  # noqa: E402
    from rich.align import Align  # type: ignore  # noqa: E402
    from rich.markdown import Markdown  # type: ignore  # noqa: E402
    from rich.traceback import Traceback  # type: ignore  # noqa: E402
except Exception as exc:
    pytest.skip("Failed to import rich from {}: {}".format(REPO_ROOT, exc), allow_module_level=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_console_buffer() -> Tuple[Console, io.StringIO]:
    buf = io.StringIO()
    console = Console(
        file=buf,
        force_terminal=True,
        color_system="truecolor",
        log_path=False,
        width=80,
    )
    return console, buf


def _get_output(buf: io.StringIO) -> str:
    out = buf.getvalue()
    assert isinstance(out, str)
    return out


# ---------------------------------------------------------------------------
# Tests (functional-only, happy path)  >= 10 test_* functions
# ---------------------------------------------------------------------------

def test_console_print_and_rule_styled_output() -> None:
    console, buf = make_console_buffer()

    console.print("[bold magenta]Hello[/bold magenta] [green]World[/green]!")
    console.rule("Section")

    output = _get_output(buf)

    assert "Hello" in output
    assert "World" in output
    assert "Section" in output
    assert "\x1b[" in output  # ANSI escape codes present


def test_table_rendering_with_title_and_rows() -> None:
    console, buf = make_console_buffer()

    table = Table(title="Planets")
    table.add_column("Name", style="cyan")
    table.add_column("Radius", style="magenta")
    table.add_column("Mass", style="green")

    table.add_row("Mercury", "2439", "3.30e23")
    table.add_row("Earth", "6371", "5.97e24")
    table.add_row("Mars", "3389", "6.42e23")

    console.print(table)

    output = _get_output(buf)
    assert "Planets" in output
    assert "Name" in output and "Radius" in output and "Mass" in output
    assert "Mercury" in output and "Earth" in output and "Mars" in output
    assert any(ch in output for ch in ("│", "┼", "+", "|"))


def test_progress_basic_task_completion() -> None:
    console, buf = make_console_buffer()

    with Progress(console=console, transient=False) as progress:
        task_id = progress.add_task("Processing", total=5)
        progress.update(task_id, completed=5)
        task = next(t for t in progress.tasks if t.id == task_id)
        assert task.completed == task.total

    output = _get_output(buf)
    assert "Processing" in output


def test_multiple_tables_and_mixed_output() -> None:
    console, buf = make_console_buffer()

    console.log("Starting mixed output test")

    users = Table(title="Users")
    users.add_column("Name")
    users.add_column("Role")
    users.add_row("Alice", "admin")
    users.add_row("Bob", "user")

    servers = Table(title="Servers")
    servers.add_column("Host")
    servers.add_column("Status")
    servers.add_row("srv-1", "OK")
    servers.add_row("srv-2", "DOWN")

    console.print(users)
    console.rule("Separator")
    console.print(servers)

    output = _get_output(buf)
    assert "Starting mixed output test" in output
    assert "Users" in output and "Servers" in output
    assert "Alice" in output and "admin" in output
    assert "srv-2" in output and "DOWN" in output
    assert "Separator" in output


def test_console_log_includes_message_text() -> None:
    console, buf = make_console_buffer()

    console.log("A log message")
    output = _get_output(buf)

    assert "A log message" in output
    # Rich log typically wraps prefix in brackets; we only check presence of bracket chars.
    assert "[" in output or "]" in output


def test_console_print_text_object_with_style() -> None:
    console, buf = make_console_buffer()

    t = Text("StyledText", style="bold red")
    console.print(t)

    output = _get_output(buf)
    assert "StyledText" in output
    assert "\x1b[" in output  # ANSI styling


def test_panel_renders_title_and_content() -> None:
    console, buf = make_console_buffer()

    panel = Panel("Inside Panel", title="PanelTitle", subtitle="PanelSub")
    console.print(panel)

    output = _get_output(buf)
    assert "Inside Panel" in output
    assert "PanelTitle" in output
    assert "PanelSub" in output
    assert any(ch in output for ch in ("┌", "┐", "└", "┘", "+", "|"))


def test_align_centers_content_visibly_present() -> None:
    console, buf = make_console_buffer()

    aligned = Align.center("Centered", vertical="middle")
    console.print(aligned)

    output = _get_output(buf)
    assert "Centered" in output


def test_columns_layout_contains_all_items() -> None:
    console, buf = make_console_buffer()

    cols = Columns(["One", "Two", "Three"], equal=True, expand=True)
    console.print(cols)

    output = _get_output(buf)
    assert "One" in output
    assert "Two" in output
    assert "Three" in output


def test_markdown_renders_heading_and_emphasis() -> None:
    console, buf = make_console_buffer()

    md = Markdown("# Heading\n\nThis is **bold** and *italic*.")
    console.print(md)

    output = _get_output(buf)
    assert "Heading" in output
    assert "bold" in output
    assert "italic" in output


def test_traceback_render_contains_exception_text() -> None:
    console, buf = make_console_buffer()

    # Create an exception and render its Rich Traceback (happy path: no asserts about raising).
    try:
        1 / 0
    except Exception as exc:
        tb = Traceback.from_exception(type(exc), exc, exc.__traceback__)
        console.print(tb)

    output = _get_output(buf)
    assert "ZeroDivisionError" in output or "division" in output.lower()
    assert "\x1b[" in output  # colored traceback usually emits ANSI codes
