# cmd2/cmd2.py

"""
Core implementation of the Cmd2 class.
"""

import cmd
from .parsing import ArgumentParser
from .utils import capture_output, TranscriptTester


class Cmd2(cmd.Cmd):
    """
    Cmd2 class extends the standard cmd.Cmd class to provide additional
    functionality such as argument parsing, transcript testing, and
    enhanced error handling.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompt = "(Cmd2) "
        self.intro = "Welcome to Cmd2! Type help or ? to list commands."

    def do_exit(self, arg):
        """Exit the application."""
        print("Exiting Cmd2.")
        return True

    def do_help(self, arg):
        """List available commands or provide detailed help for a specific command."""
        if arg:
            func = getattr(self, f"do_{arg}", None)
            if func:
                print(func.__doc__)
            else:
                print(f"No help available for '{arg}'.")
        else:
            super().do_help(arg)

    def default(self, line):
        """Handle unrecognized commands."""
        print(f"Unknown command: {line}")

    def postcmd(self, stop, line):
        """Hook method executed after every command."""
        return stop

    def cmdloop(self, intro=None):
        """Override cmdloop to handle exceptions and provide a better user experience."""
        try:
            super().cmdloop(intro)
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt. Exiting Cmd2.")
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    Cmd2().cmdloop()