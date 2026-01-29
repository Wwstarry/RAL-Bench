import pytest

from fail2ban.server.filter import isValidIP, searchIP

@pytest.mark.parametrize(
    "ip,expected",
    [
        ("1.2.3.4", True),
        ("255.255.255.255", True),
        ("2001:db8::1", True),
        ("999.1.1.1", False),
        ("1.2.3", False),
        ("2001:::1", False),
        ("1.2.3.4/24", False),
        ("[1.2.3.4]", False),
        ("fe80::1%eth0", False),
    ],
)
def test_is_valid_ip(ip, expected):
    assert isValidIP(ip) is expected

def test_search_ip_ipv4():
    line = "Failed password for root from 1.2.3.4 port 22 ssh2"
    assert searchIP(line) == "1.2.3.4"

def test_search_ip_ipv6_bracket_port():
    line = "client [2001:db8::1]:1234 connected"
    assert searchIP(line) == "2001:db8::1"

def test_search_ip_none():
    assert searchIP("no address here") is None