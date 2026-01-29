# Mailpile Core Library Slice Benchmark

This repository contains a self-contained slice of Mailpile's core library modules for benchmarking and functional testing purposes.

It includes simplified implementations of:
- `mailpile.safe_popen`: Safe subprocess wrapper and pipe helpers
- `mailpile.util`: Utilities (CleanText, base36 conversion, helpers)
- `mailpile.vcard`: VCardLine parsing and serialization
- `mailpile.i18n`: gettext passthrough helper

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install the package in editable mode with test dependencies:
   ```bash
   pip install -e .[test]
   ```

## Running Tests

To run the functional tests, use pytest:
```bash
pytest
```

## Running Benchmarks

To run the benchmarks, use pytest with the benchmark flag:
```bash
pytest --benchmark-only
```