import cmd
import sys
import shlex
import traceback
from .parsing import parse_args, parse_options
from .utils import OutputCapture

class Cmd2(cmd.Cmd):
    """
    Cmd2 class compatible with core parts of the reference Cmd2 project.
    Supports:
    - do_<command> methods
    - help_<command> methods
    - tab completion
    - error reporting
    - output capture
    """

    def __init__(self, completekey='tab', stdin=None, stdout=None):
        super().__init__(completekey=completekey, stdin=stdin, stdout=stdout)
        self._output_capture = None
        self._last_result = None
        self.use_rawinput = True
        self._stop = False

    def cmdloop(self, intro=None):
        if intro is not None:
            self.intro = intro
        self.preloop()
        if self.intro:
            self.stdout.write(str(self.intro) + '\n')
        stop = None
        while not stop:
            try:
                if self.use_rawinput:
                    line = self._readline()
                else:
                    self.stdout.write(self.prompt)
                    self.stdout.flush()
                    line = self.stdin.readline()
                    if not line:
                        line = 'EOF'
                    else:
                        line = line.rstrip('\r\n')
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            except KeyboardInterrupt:
                self.stdout.write('\nKeyboardInterrupt\n')
                self.lastcmd = ''
            except EOFError:
                self.stdout.write('\n')
                break
            except Exception:
                self.stdout.write(traceback.format_exc())
        self.postloop()

    def _readline(self):
        try:
            return input(self.prompt)
        except EOFError:
            return 'EOF'

    def onecmd(self, line):
        line = line.strip()
        if not line:
            return self.emptyline()
        cmd, arg, line = self.parseline(line)
        if not line:
            return self.emptyline()
        if cmd is None:
            return self.default(line)
        self.lastcmd = line
        self.lastparsed = (cmd, arg)
        try:
            func = getattr(self, 'do_' + cmd)
        except AttributeError:
            return self.default(line)
        try:
            ret = func(arg)
            self._last_result = ret
            return ret
        except Exception as e:
            self.perror(e)
            return False

    def parseline(self, line):
        line = line.strip()
        if not line:
            return None, None, line
        if line == 'EOF':
            return 'EOF', '', line
        if line[0] == '?':
            line = 'help ' + line[1:]
        if line[0] == '!':
            line = 'shell ' + line[1:]
        i = line.find(' ')
        if i < 0:
            cmd = line
            arg = ''
        else:
            cmd = line[:i]
            arg = line[i + 1:].strip()
        return cmd, arg, line

    def emptyline(self):
        # Do nothing on empty input line
        return False

    def default(self, line):
        self.stdout.write(f'*** Unknown syntax: {line}\n')
        return False

    def do_help(self, arg):
        "List available commands with 'help' or detailed help with 'help cmd'."
        if arg:
            # Try to call help_<command>
            try:
                func = getattr(self, 'help_' + arg)
            except AttributeError:
                self.stdout.write(f'No help on {arg}\n')
                return
            func()
        else:
            names = self.get_names()
            cmds = set()
            for name in names:
                if name.startswith('do_'):
                    cmds.add(name[3:])
            self.stdout.write('Commands:\n')
            for cmd_name in sorted(cmds):
                self.stdout.write(f'  {cmd_name}\n')

    def complete(self, text, state):
        # Override to provide tab completion for commands
        if state == 0:
            if text:
                self._completion_matches = [cmd[3:] for cmd in self.get_names()
                                            if cmd.startswith('do_' + text)]
            else:
                self._completion_matches = [cmd[3:] for cmd in self.get_names()
                                            if cmd.startswith('do_')]
        try:
            return self._completion_matches[state]
        except IndexError:
            return None

    def completenames(self, text, *ignored):
        dotext = 'do_' + text
        return [a[3:] for a in self.get_names() if a.startswith(dotext)]

    def perror(self, err):
        # Print error message to stdout
        self.stdout.write(f'Error: {err}\n')

    def set_output_capture(self, capture):
        self._output_capture = capture

    def write(self, text):
        if self._output_capture:
            self._output_capture.write(text)
        else:
            self.stdout.write(text)

    def do_EOF(self, arg):
        "Exit the command loop."
        self.stdout.write('\n')
        return True

    def do_shell(self, arg):
        "Run a shell command"
        import subprocess
        try:
            result = subprocess.run(arg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.stdout:
                self.stdout.write(result.stdout)
            if result.stderr:
                self.stdout.write(result.stderr)
        except Exception as e:
            self.perror(e)