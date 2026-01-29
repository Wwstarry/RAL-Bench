glances (minimal)

This repository provides a minimal, cross-platform subset of the Glances CLI behaviors needed by the test suite:

- python -m glances --help
- python -m glances -V / --version
- python -m glances --stdout-csv <FIELDS>

Supported CSV fields:
- now
- cpu.user
- cpu.total
- mem.used
- load