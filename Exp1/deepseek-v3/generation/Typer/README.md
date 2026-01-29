# Typer Implementation

A pure Python command-line application framework compatible with Typer's core API.

## Installation

```bash
pip install -e .
```

## Usage

```python
import typer

app = typer.Typer()

@app.command()
def hello(name: str = typer.Argument(..., help="Your name")):
    """Say hello to someone."""
    typer.echo(f"Hello {name}!")

if __name__ == "__main__":
    app()
```

## Features

- Command-line application framework
- Support for commands, arguments, and options
- Help text generation
- Exit code handling
- Testing support with CliRunner

## License

MIT