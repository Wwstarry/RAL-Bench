from fail2ban.server.jail import Jail

SSH_FAIL = r"^Failed password for .* from (?P<ip>\S+) port \d+ .*$"
IGNORE_LOCAL = r"^Failed password for invalid user .* from 127\.0\.0\.1 .*$"

def test_jail_ban_threshold_and_once():
    jail = Jail(
        name="sshd",
        failregex=[SSH_FAIL],
        maxretry=3,
        findtime=60,
        bantime=0,
    )
    ip = "1.2.3.4"
    lines = [
        f"Failed password for root from {ip} port 22 ssh2",
        f"Failed password for root from {ip} port 22 ssh2",
    ]
    assert jail.process_lines(lines, now=10)["banned"] == set()
    banned = jail.add_log_line(f"Failed password for root from {ip} port 22 ssh2", now=11)
    assert banned == [ip]
    assert jail.get_banned() == {ip}

    # Further matches do not re-ban
    banned2 = jail.add_log_line(f"Failed password for root from {ip} port 22 ssh2", now=12)
    assert banned2 == []
    assert [e["type"] for e in jail.actions.events()].count("ban") == 1

def test_jail_separate_ips_and_ignore():
    jail = Jail(
        name="sshd",
        failregex=[SSH_FAIL],
        ignoreregex=[IGNORE_LOCAL],
        maxretry=2,
        findtime=60,
        bantime=0,
    )
    # Ignored line should not count (nor ban)
    jail.add_log_line("Failed password for invalid user bob from 127.0.0.1 port 22 ssh2", now=1)
    assert jail.get_banned() == set()

    jail.add_log_line("Failed password for root from 1.1.1.1 port 22 ssh2", now=2)
    jail.add_log_line("Failed password for root from 2.2.2.2 port 22 ssh2", now=3)
    assert jail.get_banned() == set()
    assert jail.add_log_line("Failed password for root from 1.1.1.1 port 22 ssh2", now=4) == ["1.1.1.1"]
    assert jail.get_banned() == {"1.1.1.1"}

def test_findtime_pruning():
    jail = Jail(
        name="sshd",
        failregex=[SSH_FAIL],
        maxretry=2,
        findtime=5,
        bantime=0,
    )
    ip = "3.3.3.3"
    jail.add_log_line(f"Failed password for root from {ip} port 22 ssh2", now=0)
    jail.add_log_line(f"Failed password for root from {ip} port 22 ssh2", now=10)
    # First event should be pruned, so no ban
    assert jail.get_banned() == set()
    # Now another within window => ban
    assert jail.add_log_line(f"Failed password for root from {ip} port 22 ssh2", now=11) == [ip]

def test_bantime_expiry():
    jail = Jail(
        name="sshd",
        failregex=[SSH_FAIL],
        maxretry=2,
        findtime=60,
        bantime=10,
    )
    ip = "4.4.4.4"
    jail.add_log_line(f"Failed password for root from {ip} port 22 ssh2", now=1)
    assert jail.add_log_line(f"Failed password for root from {ip} port 22 ssh2", now=2) == [ip]
    assert jail.get_banned() == {ip}

    # Expiry is checked on subsequent processing
    jail.add_log_line("unrelated line", now=2 + 9.9)
    assert jail.get_banned() == {ip}
    jail.add_log_line("unrelated line", now=2 + 10.1)
    assert jail.get_banned() == set()