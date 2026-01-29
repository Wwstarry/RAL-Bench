import typing

if typing.TYPE_CHECKING:
    from mitmproxy.master import Master

master: "Master" = None  # type: ignore
log = None