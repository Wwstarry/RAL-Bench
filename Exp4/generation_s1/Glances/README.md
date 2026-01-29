This is a minimal, test-focused implementation of a subset of the Glances CLI.

Supported:
- python -m glances --help
- python -m glances -V / --version
- python -m glances --stdout-csv <FIELDS>

Allowed CSV fields:
now, cpu.user, cpu.total, mem.used, load