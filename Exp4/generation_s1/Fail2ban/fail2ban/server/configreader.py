from __future__ import annotations

import configparser
from pathlib import Path
from typing import Any

from .jail import Jail

def _split_multiline(value: str) -> list[str]:
    # ConfigParser keeps multiline values with embedded newlines; split and trim.
    parts: list[str] = []
    for line in (value or "").splitlines():
        s = line.strip()
        if not s:
            continue
        parts.append(s)
    return parts

def load_jail_conf(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))

    cp = configparser.ConfigParser(interpolation=None)
    cp.read(p, encoding="utf-8")

    defaults = dict(cp.defaults())
    jails: dict[str, dict[str, str]] = {}
    for section in cp.sections():
        jails[section] = dict(cp.items(section))

    return {"defaults": defaults, "jails": jails}

def build_jail(name: str, conf: dict[str, Any]) -> Jail:
    defaults = conf.get("defaults", {}) or {}
    jails = conf.get("jails", {}) or {}
    if name not in jails:
        raise KeyError(f"Jail section not found: {name}")

    merged: dict[str, str] = dict(defaults)
    merged.update(jails[name])

    def _get_int(key: str, default: int) -> int:
        v = merged.get(key, str(default))
        try:
            return int(str(v).strip())
        except ValueError as e:
            raise ValueError(f"Invalid integer for {key} in jail {name}: {v!r}") from e

    enabled = str(merged.get("enabled", "false")).strip().lower() in ("1", "true", "yes", "on")
    maxretry = _get_int("maxretry", 3)
    findtime = _get_int("findtime", 600)
    bantime = _get_int("bantime", 600)

    failregex = _split_multiline(merged.get("failregex", ""))
    ignoreregex = _split_multiline(merged.get("ignoreregex", ""))

    jail = Jail(
        name=name,
        failregex=failregex if failregex else None,
        ignoreregex=ignoreregex if ignoreregex else None,
        maxretry=maxretry,
        findtime=findtime,
        bantime=bantime,
    )
    # "enabled" is not used to start anything (offline-only), but keep attribute.
    jail.enabled = enabled
    return jail