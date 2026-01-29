import cmd
import os
from typing import List, Optional, Tuple

from .parsing import Statement, parse_command
from .utils import OutputCapture, StdSim, split_output_lines


class TranscriptError(AssertionError):
    """Raised when a transcript test fails due to output mismatch."""

    def __init__(self, message: str, command: Optional[str] = None, line_no: Optional[int] = None):
        super().__init__(message)
        self.command = command
        self.line_no = line_no


class Cmd2(cmd.Cmd):
    """
    Minimal Cmd2-compatible command-line application framework.

    Features:
    - Subclasses cmd.Cmd to provide traditional do_<command> handlers
    - poutput and perror for consistent formatted output
    - Tab-completion using cmd.Cmd's complete_<command> hooks
    - Transcript-based testing via run_transcript()
    - Basic exit commands: quit, exit, EOF
    - Optional stdout and stderr customization via attributes
    """

    prompt = "(Cmd2) "
    intro = None

    def __init__(self, stdin=None, stdout=None):
        super().__init__()
        # Streams
        self.stdin = stdin
        self.stdout = stdout if stdout is not None else StdSimProxyWrapper()
        self.stderr = StdSimProxyWrapper()
        # Internal state
        self._should_quit = False

    # ----- Output helpers -----
    def poutput(self, msg: object = "", end: str = "\n") -> None:
        """
        Print to the application's output stream, consistent with cmd2 semantics.
        Ensures writes go through self.stdout, not directly to sys.stdout.
        """
        try:
            text = "" if msg is None else str(msg)
            self.stdout.write(text + (end if end is not None else ""))
            try:
                self.stdout.flush()
            except Exception:
                pass
        except Exception:
            # Fallback to base print if necessary
            print(msg, end=end)

    def pfeedback(self, msg: object = "", end: str = "\n") -> None:
        """
        Alias for poutput used in cmd2 for normal user feedback.
        """
        self.poutput(msg, end=end)

    def perror(self, msg: object = "", end: str = "\n") -> None:
        """
        Print an error message to the error stream.
        """
        try:
            text = "" if msg is None else str(msg)
            self.stderr.write(text + (end if end is not None else ""))
            try:
                self.stderr.flush()
            except Exception:
                pass
        except Exception:
            print(msg, end=end)

    # ----- Exit commands -----
    def do_quit(self, arg):
        """Quit the application."""
        return True

    def do_exit(self, arg):
        """Exit the application."""
        return True

    def do_EOF(self, arg):
        """Exit on end-of-file (Ctrl-D/Ctrl-Z)."""
        self.poutput("")  # Ensure a newline similar to cmd2 default
        return True

    # ----- Command loop helpers -----
    def cmdloop(self, intro=None):
        """Run command loop until exit. Uses cmd.Cmd implementation but respects intro."""
        if intro is not None:
            self.intro = intro
        return super().cmdloop(self.intro)

    def onecmd(self, line: str) -> bool:
        """
        Execute a single command line.
        - Parses the line
        - Calls the appropriate do_<command> method
        - Returns True to exit the loop, False to continue
        """
        try:
            return super().onecmd(line)
        except KeyboardInterrupt:
            # Consistent with cmd-like behavior: print newline and continue
            self.poutput("")
            return False

    # ----- Transcript support -----
    def run_transcript(self, transcript_path: str) -> None:
        """
        Run scripted commands and compare output line-by-line against transcript.

        Format:
            Lines starting with '#', ';', or empty lines are ignored.
            A command line starts with '> ' followed by the command string.
            The lines following a command until the next command or EOF are the expected output.
            Expected output comparison is exact, line-by-line.

        Example transcript:

            # this is a comment
            > help
            Documented commands (type help <topic>):
            ========================
            EOF  exit  help  quit

            > echo hello
            hello

        Raises TranscriptError if any mismatch occurs.
        """
        if not os.path.exists(transcript_path):
            raise FileNotFoundError(f"Transcript not found: {transcript_path}")
        with open(transcript_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        blocks = self._parse_transcript_blocks(lines)
        for idx, (cmdline, expected_lines) in enumerate(blocks, start=1):
            with OutputCapture(self) as cap:
                # Execute command
                should_quit = self.onecmd(cmdline)
                # For transcript tests, ignore quit/exit results; still compare output
                actual_lines = cap.stdout_lines
                # Drop final empty line if last write added an extra newline?
                # We do not strip; compare exactly as produced.
            # Compare actual output to expected
            self._compare_transcript_output(
                cmdline=cmdline,
                expected=expected_lines,
                actual=actual_lines,
                block_no=idx,
            )

    def _parse_transcript_blocks(self, lines: List[str]) -> List[Tuple[str, List[str]]]:
        """
        Parse transcript file lines into list of (command, expected_output_lines) tuples.
        """
        blocks: List[Tuple[str, List[str]]] = []
        current_cmd: Optional[str] = None
        current_expected: List[str] = []
        for raw in lines:
            line = raw.rstrip("\n")
            if not line.strip():
                # blank line indicates end of expected block; preserve blank lines within expected
                if current_cmd is not None:
                    # Include the blank line in expected output
                    current_expected.append("")
                continue
            if line.startswith("#") or line.startswith(";"):
                # comment - ignore
                continue
            if line.startswith("> "):
                # New command starts
                if current_cmd is not None:
                    blocks.append((current_cmd, current_expected))
                current_cmd = line[2:].strip()
                current_expected = []
            else:
                # Expected output line
                if current_cmd is None:
                    # If expected output occurs before any command, ignore
                    continue
                current_expected.append(line)
        # Add last block
        if current_cmd is not None:
            blocks.append((current_cmd, current_expected))
        return blocks

    def _compare_transcript_output(
        self,
        cmdline: str,
        expected: List[str],
        actual: List[str],
        block_no: int,
    ) -> None:
        """
        Compare actual output lines to expected, raise TranscriptError on mismatch.
        """
        # Normalize trailing empty line differences: many commands print a trailing newline
        # We compare lengths exactly for strictness required by tests.
        max_len = max(len(expected), len(actual))
        for i in range(max_len):
            exp = expected[i] if i < len(expected) else None
            got = actual[i] if i < len(actual) else None
            if exp != got:
                where = f"block {block_no}, line {i+1}"
                raise TranscriptError(
                    f"Transcript mismatch at {where} for command '{cmdline}': expected {repr(exp)}, got {repr(got)}",
                    command=cmdline,
                    line_no=i + 1,
                )

    # ----- Convenience methods to integrate with parsing utilities -----
    def statement_parser(self, line: str) -> Statement:
        """Return a Statement object parsed from the input line."""
        return parse_command(line)


class StdSimProxyWrapper(StdSim):
    """
    A StdSim that tries to mimic file-like attributes commonly used by cmd.Cmd,
    including name and isatty compatibility.
    """

    def __init__(self):
        super().__init__()
        self.name = "<StdSim>"

    def isatty(self):
        return False