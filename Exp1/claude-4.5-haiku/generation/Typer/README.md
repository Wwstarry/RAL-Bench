# Typer

A pure Python command-line interface framework that is API-compatible with the core parts of the reference Typer project.

## Features

- Simple API for building CLI applications
- Support for multiple commands
- Options and arguments with defaults
- Help text generation
- Testing utilities

## Installation

```bash
pip install -e .
```

## Usage

```python
import typer

app = typer.Typer()

@app.command()
def hello(name: str = typer.Option(..., help="Name to greet")):
    """Say hello to someone."""
    typer.echo(f"Hello {name}!")

if __name__ == "__main__":
    app()
```

## Testing

```python
from typer.testing import CliRunner

runner = CliRunner()
result = runner.invoke(app, ["hello", "--name", "World"])
assert result.exit_code == 0
assert "Hello World!" in result.output
```