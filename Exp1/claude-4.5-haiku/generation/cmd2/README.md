# cmd2

A pure Python interactive command-line application framework that is API-compatible with the core parts of the reference Cmd2 project.

## Features

- Subclasses `cmd.Cmd` for familiar command-line interface
- Command registration via `do_<name>` methods
- Automatic help generation
- Tab-completion hooks
- Output capture and transcript support
- Error reporting and debugging
- Script execution support

## Installation

```bash
pip install -e .
```

## Quick Start

```python
import cmd2

class MyApp(cmd2.Cmd2):
    """Simple command-line application."""
    
    def do_hello(self, args):
        """Say hello"""
        self.poutput(f"Hello {args or 'World'}!")
    
    def do_exit(self, args):
        """Exit the application"""
        return True

if __name__ == '__main__':
    app = MyApp()
    app.cmdloop()
```

## API

### Cmd2 Class

The main class for building command-line applications.

#### Methods

- `onecmd(line)` - Execute a single command
- `poutput(msg)` - Print output to stdout
- `perror(msg)` - Print error output to stderr
- `pfeedback(msg)` - Print feedback message
- `cmdloop(intro)` - Run the command loop
- `get_all_commands()` - Get list of all available commands
- `get_command_help(command)` - Get help text for a command
- `run_script(script_path)` - Run commands from a script file
- `capture_output(func, *args, **kwargs)` - Capture output from a function call

### Parsing Module

Utilities for parsing command-line arguments.

- `parse_command_line(line)` - Parse a command line
- `split_args(args)` - Split arguments respecting quotes
- `ParsedString` - Represents a parsed command string

### Utils Module

Utility functions.

- `safe_str(obj)` - Safely convert object to string
- `strip_ansi(text)` - Remove ANSI color codes
- `format_table(rows, headers)` - Format data as a table
- `OutputCapture` - Context manager for capturing output

## License

MIT