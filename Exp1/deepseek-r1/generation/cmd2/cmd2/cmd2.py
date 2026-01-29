import sys
import cmd
import shlex
from .utils import StdSim, OutputRecorder
from .parsing import Statement, parse_arguments

class Cmd2(cmd.Cmd):
    """Command interpreter with enhanced features for output capturing."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self._output_recorder = OutputRecorder()
        self._transcript_target = None

    def precmd(self, line):
        """Process input line before execution."""
        self._output_recorder.start()
        return line

    def postcmd(self, stop, line):
        """Process after command execution."""
        captured = self._output_recorder.stop()
        if self._transcript_target:
            self._transcript_target.write(f"{line}\n{captured}\n")
        return stop

    def onecmd(self, line):
        """Execute single command with output capturing."""
        try:
            return super().onecmd(line)
        except Exception as e:
            self.stdout.write(f"Error: {str(e)}\n")
            return False

    def do_help(self, arg):
        """Display help documentation."""
        if arg:
            try:
                doc = getattr(self, f'help_{arg}').__doc__
                if doc:
                    self.stdout.write(f"{doc}\n")
                    return
            except AttributeError:
                pass
        super().do_help(arg)

    def default(self, line):
        """Handle unknown commands."""
        self.stdout.write(f"Unknown command: {line.split()[0]}\n")

    def run_transcript(self, commands):
        """Execute commands sequentially for transcript testing."""
        self._transcript_target = []
        for cmd in commands:
            self.onecmd(cmd)
        transcript = ''.join(self._transcript_target)
        self._transcript_target = None
        return transcript

    def complete(self, text, state):
        """Tab completion handler."""
        return super().complete(text, state)