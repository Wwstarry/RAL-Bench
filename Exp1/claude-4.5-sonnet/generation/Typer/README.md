# Typer

A pure Python command-line application framework.

## Installation

```bash
pip install -e .
```

## Usage

```python
import typer

app = typer.Typer()

@app.command()
def hello(name: str):
    typer.echo(f"Hello {name}")

if __name__ == "__main__":
    app()
```

## Features

- Simple API for building CLI applications
- Support for commands, options, and arguments
- Built-in help generation
- Testing utilities

## API

- `typer.Typer`: Main application class
- `typer.Option`: Define CLI options
- `typer.Argument`: Define CLI arguments
- `typer.echo`: Print to console
- `typer.Exit`: Exit with specific code
- `typer.testing.CliRunner`: Test runner for CLI apps