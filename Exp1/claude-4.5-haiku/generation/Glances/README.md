# Glances

A cross-platform system monitoring tool written in Python.

## Installation

```bash
pip install -e .
```

## Usage

### Command Line

Display help:
```bash
python -m glances --help
```

Display version:
```bash
python -m glances --version
```

Output CSV data:
```bash
python -m glances --stdout-csv now,cpu.user,mem.used,load
```

### As a Module

```python
from glances.core import GlancesCore

core = GlancesCore()
print(core.get_field("cpu.user"))
print(core.get_field("mem.used"))
```

## Supported CSV Fields

- `now` - Current timestamp in ISO format
- `cpu.user` - CPU user time
- `cpu.total` - Total CPU time
- `cpu.percent` - CPU usage percentage
- `mem.used` - Used memory in bytes
- `mem.total` - Total memory in bytes
- `mem.percent` - Memory usage percentage
- `load` - Load average (1-minute)

## Requirements

- Python 3.6+
- psutil