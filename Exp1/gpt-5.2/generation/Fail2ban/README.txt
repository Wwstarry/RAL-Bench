Minimal safe-to-evaluate subset of Fail2Ban (offline).

Included:
- fail2ban.server.jail.Jail: processes log lines with failregex and tracks "banned" IPs in memory.
- fail2ban.server.filter: IP helpers (isValidIP/searchIP) and minimal FailRegex.
- config/jail.conf: canonical config artifact.
- bin/fail2ban-client, bin/fail2ban-server: stubs for --help/--version only.
- bin/fail2ban-regex: offline regex scanner for log files (no root, no firewall changes).