This is a minimal, test-focused implementation of a subset of the Glances CLI behaviors.

Supported:
- python -m glances --help
- python -m glances -V / --version
- python -m glances --stdout-csv <FIELDS>

CSV fields supported:
- now
- cpu.user
- cpu.total
- mem.used
- load