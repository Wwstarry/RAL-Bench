import tempfile
from fail2ban.server.jail import Jail

def test_jail_banning():
    jail = Jail("sshd", r"Failed password for .* from (\d+\.\d+\.\d+\.\d+)", maxretry=2)
    log_lines = [
        "Jan 1 00:00:01 server sshd[123]: Failed password for root from 1.2.3.4 port 22 ssh2",
        "Jan 1 00:00:02 server sshd[123]: Failed password for root from 1.2.3.4 port 22 ssh2",
        "Jan 1 00:00:03 server sshd[123]: Failed password for root from 5.6.7.8 port 22 ssh2",
    ]
    banned = []
    for line in log_lines:
        ip, is_banned = jail.process_line(line)
        if is_banned:
            banned.append(ip)
    assert "1.2.3.4" in banned
    assert "5.6.7.8" not in banned
    assert jail.get_banned() == ["1.2.3.4"]

def test_jail_reset():
    jail = Jail("sshd", r"Failed password for .* from (\d+\.\d+\.\d+\.\d+)", maxretry=1)
    jail.process_line("Jan 1 00:00:01 server sshd[123]: Failed password for root from 9.8.7.6 port 22 ssh2")
    assert jail.get_banned() == ["9.8.7.6"]
    jail.reset()
    assert jail.get_banned() == []