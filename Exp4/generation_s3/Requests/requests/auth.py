from __future__ import annotations

import base64


class AuthBase:
    def __call__(self, r):
        return r


class HTTPBasicAuth(AuthBase):
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def __call__(self, r):
        # Do not override if already present
        if r.headers.get("Authorization") is None:
            token = f"{self.username}:{self.password}".encode("utf-8")
            b64 = base64.b64encode(token).decode("ascii")
            r.headers["Authorization"] = f"Basic {b64}"
        return r