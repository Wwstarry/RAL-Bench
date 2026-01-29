# Glances - Cross-platform System Monitoring Tool

A Python implementation of a system monitoring tool compatible with Glances CLI behavior.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Show help
python -m glances --help

# Show version
python -m glances --version

# One-shot CSV output
python -m glances --stdout-csv now,cpu.user,mem.used,load
```

## Supported CSV Fields

- `now`: Current timestamp
- `cpu.user`: CPU user percentage
- `cpu.total`: Total CPU usage percentage
- `mem.used`: Used memory in bytes
- `load`: System load average

## License

LGPL