"""Type definitions for TheFuck."""


class Command:
    """Represents a console command with its output and exit code."""
    
    def __init__(self, script, output='', stderr='', exit_code=1):
        """Initialize a Command.
        
        Args:
            script: The command line string
            output: Standard output from the command
            stderr: Standard error from the command (optional, defaults to output)
            exit_code: Exit code of the command
        """
        self.script = script
        self.output = output
        self.stderr = stderr if stderr else output
        self.exit_code = exit_code
    
    def __repr__(self):
        return f'Command(script={self.script!r}, output={self.output!r})'
    
    def __eq__(self, other):
        if not isinstance(other, Command):
            return False
        return (self.script == other.script and 
                self.output == other.output and
                self.stderr == other.stderr and
                self.exit_code == other.exit_code)