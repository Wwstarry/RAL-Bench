from pathlib import Path

from fail2ban.server.configreader import load_jail_conf, build_jail

def test_config_exists_and_parses():
    root = Path(__file__).resolve().parents[1]
    conf_path = root / "config" / "jail.conf"
    assert conf_path.exists()

    conf = load_jail_conf(str(conf_path))
    assert "defaults" in conf and "jails" in conf
    assert "sshd" in conf["jails"]

def test_build_jail_from_conf():
    root = Path(__file__).resolve().parents[1]
    conf_path = root / "config" / "jail.conf"
    conf = load_jail_conf(str(conf_path))
    jail = build_jail("sshd", conf)

    assert jail.name == "sshd"
    assert jail.maxretry == 3
    assert jail.findtime == 120
    assert jail.bantime == 60
    assert jail.failregex and isinstance(jail.failregex, list)
    assert hasattr(jail, "enabled") and jail.enabled is True