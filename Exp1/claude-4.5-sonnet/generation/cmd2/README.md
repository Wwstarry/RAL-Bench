# cmd2

A pure Python interactive command-line application framework that is API-compatible with core parts of the reference Cmd2 project.

## Features

- Command-line interpreter based on Python's `cmd` module
- Enhanced command parsing and argument handling
- Support for command shortcuts and aliases
- Output redirection and capture utilities
- Transcript-based testing support
- Help system with automatic documentation generation

## Installation

```bash
pip install .
```

## Quick Start

```python
import cmd2

class MyApp(cmd2.Cmd):
    """A simple cmd2 application"""
    
    def do_greet(self, args):
        """Greet someone"""
        name = args or 'World'
        self.poutput(f'Hello, {name}!')
        
    def do_exit(self, args):
        """Exit the application"""
        return True

if __name__ == '__main__':
    app = MyApp()
    app.cmdloop()
```

## API Compatibility

This implementation provides compatibility with core cmd2 features:

- `Cmd` class (exposed as `Cmd2`)
- `Statement` parsing class
- Output utilities (`poutput`, `perror`, `pfeedback`)
- Transcript testing support
- Command registration via `do_<name>` methods
- Help generation via docstrings

## Testing

The framework supports transcript-based testing where scripted commands are run and output is compared:

```python
app = cmd2.Cmd(transcript_files=['test_transcript.txt'])
app.cmdloop()
```

## License

MIT License