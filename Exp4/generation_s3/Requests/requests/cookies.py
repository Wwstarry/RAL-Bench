from __future__ import annotations

from http.cookies import SimpleCookie


class RequestsCookieJar(dict):
    """
    Minimal cookie jar supporting dict-like access and simple Cookie header rendering.
    Ignores domain/path scoping; suitable for local test servers.
    """

    def set(self, name, value):
        self[name] = value

    def get_cookie_header(self):
        if not self:
            return None
        # Simple "name=value; name2=value2"
        return "; ".join([f"{k}={v}" for k, v in self.items()])

    def update_from_cookie_header(self, cookie_header: str | None):
        if not cookie_header:
            return
        c = SimpleCookie()
        try:
            c.load(cookie_header)
        except Exception:
            return
        for k, morsel in c.items():
            self[k] = morsel.value

    def update_from_set_cookie_headers(self, set_cookie_headers):
        if not set_cookie_headers:
            return
        if isinstance(set_cookie_headers, (str, bytes)):
            set_cookie_headers = [set_cookie_headers]
        for h in set_cookie_headers:
            if isinstance(h, bytes):
                try:
                    h = h.decode("iso-8859-1", errors="replace")
                except Exception:
                    continue
            self.update_from_cookie_header(h)


def cookiejar_from_dict(d: dict | None):
    jar = RequestsCookieJar()
    if d:
        for k, v in d.items():
            jar[str(k)] = str(v)
    return jar


def merge_cookies(jar: RequestsCookieJar, cookies):
    if cookies is None:
        return jar
    out = RequestsCookieJar()
    out.update(jar or {})
    if isinstance(cookies, RequestsCookieJar):
        out.update(cookies)
    elif isinstance(cookies, dict):
        for k, v in cookies.items():
            out[str(k)] = str(v)
    else:
        # Unknown type; best effort: try dict()
        try:
            out.update(dict(cookies))
        except Exception:
            pass
    return out