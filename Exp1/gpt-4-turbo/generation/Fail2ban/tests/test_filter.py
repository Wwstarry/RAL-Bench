from fail2ban.server.filter import isValidIP, searchIP, findAllIPs

def test_isValidIP():
    assert isValidIP("127.0.0.1")
    assert isValidIP("::1")
    assert not isValidIP("999.999.999.999")
    assert not isValidIP("not.an.ip")

def test_searchIP():
    line = "Failed password for root from 192.168.1.10 port 22 ssh2"
    assert searchIP(line) == "192.168.1.10"
    line2 = "Connection from ::1 port 12345"
    assert searchIP(line2) == "::1"
    line3 = "No IP here"
    assert searchIP(line3) is None

def test_findAllIPs():
    line = "IPs: 10.0.0.1, 192.168.1.1 and ::1"
    ips = findAllIPs(line)
    assert "10.0.0.1" in ips
    assert "192.168.1.1" in ips
    assert "::1" in ips