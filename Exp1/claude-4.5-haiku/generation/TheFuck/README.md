# TheFuck

A pure Python implementation of TheFuck - auto-corrects your previous console command.

## Installation

```bash
pip install -e .
```

## Usage

```bash
python -m thefuck <command>
```

Or after installation:

```bash
thefuck <command>
```

## Features

- Auto-detects common command errors
- Suggests corrections based on error patterns
- Extensible rule system for adding new correction patterns

## Development

```bash
python -m pytest tests/
```