from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple


@dataclass
class Option:
    name: str
    default: Any
    typespec: Optional[type] = None
    help: str = ""


class Options:
    """
    Minimal options store with attribute and mapping-like access.

    Unknown options are permitted and tracked.
    """

    def __init__(self, **kwargs: Any):
        self._defs: Dict[str, Option] = {}
        self._values: Dict[str, Any] = {}

        # Define minimal standard options expected by cmdline/frontends.
        self.add_option("verbose", 0, int, help="Increase verbosity.")
        self.add_option("quiet", False, bool, help="Quiet mode.")
        self.add_option("mode", "regular", str, help="Proxy mode.")
        self.add_option("listen_host", "127.0.0.1", str, help="Listen host.")
        self.add_option("listen_port", 8080, int, help="Listen port.")
        self.add_option("confdir", "", str, help="Configuration directory.")
        self.add_option("set", [], list, help="Set option: KEY=VALUE.")
        self.add_option("scripts", [], list, help="Addon scripts (not executed).")

        self.update(**kwargs)

    def add_option(self, name: str, default: Any, typespec: Optional[type] = None, help: str = "") -> None:
        if name in self._defs:
            # keep deterministic: do not overwrite existing
            return
        self._defs[name] = Option(name=name, default=default, typespec=typespec, help=help or "")
        self._values.setdefault(name, default)

    def update(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            self[k] = v

    def keys(self) -> Iterable[str]:
        return self._values.keys()

    def get_help(self) -> List[Tuple[str, Any, str]]:
        """
        Return a stable, minimal help listing for registered options.
        """
        out: List[Tuple[str, Any, str]] = []
        for name in sorted(self._defs.keys()):
            opt = self._defs[name]
            out.append((opt.name, opt.default, opt.help))
        return out

    def __getattr__(self, item: str) -> Any:
        # called only if normal attribute lookup fails
        if item in self._values:
            return self._values[item]
        raise AttributeError(item)

    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith("_"):
            object.__setattr__(self, key, value)
        else:
            self.__setitem__(key, value)

    def __getitem__(self, key: str) -> Any:
        return self._values[key]

    def __setitem__(self, key: str, value: Any) -> None:
        # If defined and has a typespec, attempt a lightweight conversion.
        opt = self._defs.get(key)
        if opt and opt.typespec and value is not None:
            # Be permissive: accept already-correct types.
            try:
                if opt.typespec is bool:
                    if isinstance(value, str):
                        value = value.lower() in ("1", "true", "yes", "on")
                    else:
                        value = bool(value)
                elif opt.typespec is int:
                    value = int(value)
                elif opt.typespec is str:
                    value = str(value)
                elif opt.typespec is list:
                    if value is None:
                        value = []
                    elif isinstance(value, list):
                        pass
                    else:
                        value = [value]
                else:
                    # generic attempt
                    value = opt.typespec(value)
            except Exception:
                # Keep minimal; store raw value if conversion fails.
                pass

        # Unknown options are allowed: track value anyway.
        self._values[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._values

    def __repr__(self) -> str:
        return f"Options({self._values!r})"