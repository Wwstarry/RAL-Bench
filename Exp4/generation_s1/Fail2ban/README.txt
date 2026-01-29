This repository implements a minimal, offline-safe subset of Fail2Ban.

Scope:
- Regex-based log line matching and IP extraction (IPv4/IPv6).
- In-memory ban tracking with maxretry/findtime/bantime logic.
- Minimal configuration reader for config/jail.conf.
- CLI tools are stubs or offline utilities; they must not start daemons, open sockets, or modify firewall rules.

Safety:
- No root required.
- No firewall changes.
- No daemon or networking.

Provided scripts:
- bin/fail2ban-regex: offline regex tester against a log file (or stdin).
- bin/fail2ban-client: help/version only (no server communication).
- bin/fail2ban-server: help only; explicitly does not start any daemon.