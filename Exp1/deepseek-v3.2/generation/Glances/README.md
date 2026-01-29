# Glances

A cross-platform system monitoring tool compatible with the Glances CLI interface.

## Installation

```bash
pip install -e .
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
- `cpu.total`: CPU total percentage  
- `mem.used`: Memory used percentage
- `load`: System load average (1-minute)

## License

LGPL v3