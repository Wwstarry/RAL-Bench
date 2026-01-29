"""
Global context placeholder, as commonly used by mitmproxy addons.

In real mitmproxy, ctx is populated by the running master instance.
Here we provide only the minimal attributes used by addons/tests.
"""


class _Ctx:
    def __init__(self) -> None:
        self.master = None
        self.options = None

    def __repr__(self) -> str:
        return f"<mitmproxy.ctx master={type(self.master).__name__} options={type(self.options).__name__}>"


ctx = _Ctx()

__all__ = ["ctx"]