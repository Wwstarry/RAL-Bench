import base64


class AuthBase:
    def __call__(self, r):
        return r


class HTTPBasicAuth(AuthBase):
    def __init__(self, username, password):
        self.username = "" if username is None else str(username)
        self.password = "" if password is None else str(password)

    def __call__(self, r):
        token = f"{self.username}:{self.password}".encode("utf-8")
        b64 = base64.b64encode(token).decode("ascii")
        r.headers["Authorization"] = f"Basic {b64}"
        return r