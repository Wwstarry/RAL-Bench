import base64


class AuthBase:
    def __call__(self, r):
        raise NotImplementedError("Auth hooks must be callable")


class HTTPBasicAuth(AuthBase):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __call__(self, r):
        userpass = f"{self.username}:{self.password}".encode("latin1")
        token = base64.b64encode(userpass).decode("ascii")
        r.headers["Authorization"] = f"Basic {token}"
        return r


def _basic_auth_str(username, password):
    userpass = f"{username}:{password}".encode("latin1")
    token = base64.b64encode(userpass).decode("ascii")
    return f"Basic {token}"