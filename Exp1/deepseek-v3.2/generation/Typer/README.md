# Typer Compat

A minimal Typer-compatible CLI framework implementation.

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

## Testing

```python
from typer.testing import CliRunner

runner = CliRunner()
result = runner.invoke(app, ["hello", "World"])
assert result.exit_code == 0
assert "Hello World!" in result.stdout
```

## Compatibility

This implementation aims to be API-compatible with the core parts of Typer for the purposes of the test suite.