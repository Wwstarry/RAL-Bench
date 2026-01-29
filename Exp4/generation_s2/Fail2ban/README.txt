This is a minimal, safe-to-evaluate subset of Fail2Ban.

What it includes:
- fail2ban.server.jail.Jail: in-memory failure tracking and banning logic (no firewall changes)
- fail2ban.server.filter: IP parsing helpers (isValidIP, searchIP, findAllIPs)
- bin/fail2ban-regex: offline regex tester for log files / text
- bin/fail2ban-client, bin/fail2ban-server: safe stubs that only provide --help/--version
- config/jail.conf: canonical config entrypoint artifact

Safety:
- No root required
- No network, no daemon, no firewall modifications