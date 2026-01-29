"""
A **tiny** re-implementation of the essential parts of ``cmd2.Cmd`` that
are needed by the black-box test-suite shipped with this repository.

Only the pieces that the tests explicitly touch have been ported – no
attempt is made to be fully feature-complete with the upstream project.
"""
from __future__ import annotations

import cmd
import contextlib
import io
import os
import sys
from typing import Iterable, Iterator, List, Optional, Sequence, Tuple

from .utils import capture_output


class Statement:
    """
    A *very* small representation of a parsed command line that mimics
    what ``cmd2`` usually returns from its parser.

    Parameters
    ----------
    command : str
        The bare command name (usually derived from the ``do_`` method
        that will be invoked).
    args : Sequence[str]
        Positional arguments that followed the command.
    """
    def __init__(self, command: str, args: Sequence[str] | None = None):
        self.command: str = command
        self.args: Tuple[str, ...] = tuple(args or ())

    def __iter__(self) -> Iterator[str]:
        return iter(self.args)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Statement(command={self.command!r}, args={self.args!r})"


class Cmd2(cmd.Cmd):
    """
    A boiled-down variant of the original ``cmd2.Cmd`` class.

    The main focus is to keep backwards compatibility for:

    * Sub-classing and overriding ``do_<command>`` handlers.
    * Enabling `with self.capture_output(): ...` context-manager usage.
    * Running a transcript test via :meth:`run_transcript`.
    """

    # Upstream uses ``use_ipython=False`` and many other options.  We
    # only implement the subset that the tests rely on.
    def __init__(
        self,
        *,
        use_readline: bool = True,
        completekey: str = "tab",
        stdin=None,
        stdout=None,
    ):
        # The base ``cmd.Cmd`` accepts (completekey, stdin, stdout)
        super().__init__(completekey=completekey, stdin=stdin, stdout=stdout)
        self.use_rawinput: bool = stdin is None  # `cmd`'s own default
        self.use_readline: bool = use_readline
        self.prompt: str = "cmd2> "
        self.intro: Optional[str] = None

        # Expose the capture-output context manager on the instance so
        # that existing patterns such as `self.capture_output()` work.
        # (We just curry the generic utility so that `self` is bound.)
        self.capture_output = contextlib.partial(capture_output, self)

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------
    def poutput(self, *objects, sep=" ", end="\n", file=None):
        """
        Convenience wrapper around ``print`` that honours the command's
        configured ``stdout`` while also allowing injection of a
        different target via *file*.
        """
        if file is None:
            file = self.stdout
        print(*objects, sep=sep, end=end, file=file)

    def perror(self, message: str):
        """
        Print an error string to ``stderr`` (or ``stdout`` if ``stderr``
        is unavailable, which can happen with redirected output during
        tests).
        """
        err_stream = getattr(self, "stderr", self.stdout)
        print(message, file=err_stream)

    # ------------------------------------------------------------------
    # Built-in commands
    # ------------------------------------------------------------------
    def do_EOF(self, _: str):
        """Handle Ctrl-D / ``EOF`` by returning True to stop the loop."""
        self.poutput("")
        return True  # Causes cmdloop to exit

    # ------------------------------------------------------------------
    # Transcript testing
    # ------------------------------------------------------------------
    def run_transcript(
        self,
        transcript_path: str | os.PathLike[str],
        *,
        dynamic: bool = False,           # Ignored – kept for API parity
        raise_exceptions: bool = False,  # Best effort implementation
    ) -> bool:
        """
        Replay the commands stored in *transcript_path* and verify that
        the line-by-line output matches the reference lines that follow
        each command.

        The expected format is identical to cmd2's own:

            cmd2> <command line>
            <expected output 1>
            <expected output 2>
            cmd2> <next command>

        The comparison is strict – whitespace and exact text must match.
        """
        transcript_path = os.fspath(transcript_path)

        with open(transcript_path, "r", encoding="utf-8") as fp:
            raw_lines = [ln.rstrip("\n") for ln in fp]

        # A tiny state machine that groups (command, expected_output)
        blocks: list[tuple[str, list[str]]] = []
        current_cmd: Optional[str] = None
        current_expected: list[str] = []
        prompt_marker = self.prompt.rstrip()

        def flush():
            nonlocal current_cmd, current_expected
            if current_cmd is not None:
                blocks.append((current_cmd, current_expected))
            current_cmd = None
            current_expected = []

        for ln in raw_lines:
            if ln.startswith(prompt_marker):
                # Found a new command
                flush()
                current_cmd = ln[len(prompt_marker):].lstrip()
            else:
                current_expected.append(ln)
        flush()

        failures: list[str] = []

        for cmd_index, (command, expected_lines) in enumerate(blocks, start=1):
            try:
                with self.capture_output() as (out, err):
                    stop = self.onecmd(command)
                    # Do **not** enter cmdloop, just run a single cmd.
                    # If a command requests application exit we honour
                    # it but keep running through the transcript so
                    # that we can report the mismatch to the caller.
                    if stop:
                        break
                output_lines = out.getvalue().rstrip("\n").splitlines()
            except Exception as exc:  # pragma: no cover – generic safety
                if raise_exceptions:
                    raise
                failures.append(
                    f"Command {cmd_index!r} raised unexpected exception: {exc}"
                )
                continue

            if output_lines != expected_lines:
                msg = [
                    f"Mismatch in command {cmd_index}: {command!r}",
                    "Expected:",
                    *("    " + ln for ln in expected_lines or ["<no output>"]),
                    "Received:",
                    *("    " + ln for ln in output_lines or ["<no output>"]),
                ]
                failures.append("\n".join(msg))

        if failures:
            for msg in failures:
                self.perror(msg)
            return False
        return True


# ----------------------------------------------------------------------
# Backwards-compatibility shims at **module** level
# ----------------------------------------------------------------------
Cmd = Cmd2                      # Alias used by many external scripts
Statement = Statement           # Re-export for `from cmd2 import Statement`
run_transcript = Cmd2.run_transcript