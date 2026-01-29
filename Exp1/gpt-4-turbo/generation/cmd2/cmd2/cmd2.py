import sys
import cmd
import traceback
import shlex
from . import parsing
from . import utils

class Cmd2(cmd.Cmd):
    """A Cmd2-compatible command interpreter."""

    prompt = "(Cmd2) "
    intro = None
    use_rawinput = True

    def __init__(self, completekey='tab', stdin=None, stdout=None):
        super().__init__(completekey=completekey, stdin=stdin, stdout=stdout)
        self._transcript_mode = False
        self._transcript_outputs = []
        self._lastcmd = None
        self._stop_transcript = False

    def onecmd(self, line):
        """Override to add error handling and transcript support."""
        line = line.strip()
        if not line:
            return self.emptyline()
        self._lastcmd = line
        try:
            stop = super().onecmd(line)
            if self._transcript_mode:
                self._transcript_outputs.append(self._get_last_output())
            return stop
        except Exception as e:
            self.perror(str(e))
            if self._transcript_mode:
                self._transcript_outputs.append(self._get_last_output())
            if hasattr(self, 'raise_exceptions') and self.raise_exceptions:
                raise
            else:
                traceback.print_exc(file=self.stdout)
            return False

    def emptyline(self):
        """Do nothing on empty input line."""
        pass

    def default(self, line):
        """Called on an input line when the command prefix is not recognized."""
        self.perror(f'*** Unknown syntax: {line}')

    def precmd(self, line):
        """Hook method executed just before the command line is interpreted."""
        return line

    def postcmd(self, stop, line):
        """Hook method executed just after a command dispatch is finished."""
        return stop

    def parseline(self, line):
        """Parse the line into command, arg, and line."""
        return super().parseline(line)

    def perror(self, msg, end='\n'):
        """Print error message to stderr."""
        print(msg, file=sys.stderr, end=end)

    def poutput(self, msg, end='\n'):
        """Print output message to stdout."""
        print(msg, file=self.stdout, end=end)

    def do_help(self, arg):
        """List available commands with "help" or detailed help with "help cmd"."""
        if arg:
            func = getattr(self, 'do_' + arg, None)
            if func:
                doc = func.__doc__
                if doc:
                    self.poutput(doc.strip())
                else:
                    self.poutput(f'No help available for {arg}')
            else:
                self.poutput(f'No such command: {arg}')
        else:
            names = self.get_names()
            cmds = sorted(set([name[3:] for name in names if name.startswith('do_')]))
            self.poutput("Documented commands (type help <topic>):")
            self.poutput("========================================")
            for cmdname in cmds:
                func = getattr(self, 'do_' + cmdname)
                if func.__doc__:
                    self.poutput(f"{cmdname}\t{func.__doc__.strip().splitlines()[0]}")
                else:
                    self.poutput(f"{cmdname}")

    def completedefault(self, text, line, begidx, endidx):
        """Default completion method."""
        return []

    def completenames(self, text, *ignored):
        """Complete command names."""
        dotext = 'do_' + text
        return [a[3:] for a in self.get_names() if a.startswith(dotext)]

    def complete_help(self, text, line, begidx, endidx):
        """Tab completion for help command."""
        return self.completenames(text)

    def cmdloop(self, intro=None):
        """Override to support transcript mode."""
        if intro is not None:
            self.intro = intro
        if self.intro:
            self.poutput(self.intro)
        try:
            super().cmdloop()
        except KeyboardInterrupt:
            self.poutput("\nKeyboardInterrupt")
        except Exception as e:
            self.perror(str(e))
            traceback.print_exc(file=self.stdout)

    def run_transcript(self, transcript_path):
        """Run commands from a transcript file and compare output line-by-line."""
        self._transcript_mode = True
        self._transcript_outputs = []
        self._stop_transcript = False
        with open(transcript_path, 'r') as f:
            lines = f.readlines()
        expected_outputs = []
        commands = []
        for line in lines:
            line = line.rstrip('\n')
            if line.startswith('>'):
                commands.append(line[1:].strip())
            else:
                expected_outputs.append(line)
        actual_outputs = []
        for cmdline in commands:
            self.onecmd(cmdline)
            output = self._get_last_output()
            actual_outputs.append(output)
        self._transcript_mode = False
        # Compare expected_outputs and actual_outputs line-by-line
        success = True
        for idx, (exp, act) in enumerate(zip(expected_outputs, actual_outputs)):
            if exp != act:
                self.perror(f"Transcript mismatch at line {idx+1}: expected '{exp}', got '{act}'")
                success = False
        if len(expected_outputs) != len(actual_outputs):
            self.perror("Transcript output length mismatch.")
            success = False
        return success

    def _get_last_output(self):
        # This is a stub for output capture; in real cmd2, output is captured more robustly.
        # Here, we just return the last output if poutput was called.
        # For compatibility, we can extend this with a buffer if needed.
        return ""  # Placeholder for output capture

    # Output capture context manager for testing
    def capture_output(self):
        return utils.OutputCapture(self)