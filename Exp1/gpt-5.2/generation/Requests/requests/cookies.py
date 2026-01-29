from http.cookies import SimpleCookie


class RequestsCookieJar:
    def __init__(self):
        self._cookies = {}  # (domain, path, name) -> value

    def set(self, name, value, domain="", path="/"):
        key = (domain or "", path or "/", name)
        self._cookies[key] = value

    def get(self, name, default=None, domain=None, path=None):
        for (d, p, n), v in self._cookies.items():
            if n != name:
                continue
            if domain is not None and d != domain:
                continue
            if path is not None and p != path:
                continue
            return v
        return default

    def update_from_set_cookie_headers(self, set_cookie_headers, request_host):
        if not set_cookie_headers:
            return
        if isinstance(set_cookie_headers, str):
            set_cookie_headers = [set_cookie_headers]
        for h in set_cookie_headers:
            c = SimpleCookie()
            try:
                c.load(h)
            except Exception:
                continue
            for morsel in c.values():
                name = morsel.key
                value = morsel.value
                domain = morsel["domain"] or request_host or ""
                path = morsel["path"] or "/"
                self.set(name, value, domain=domain, path=path)

    def cookie_header_for(self, host, path="/"):
        pairs = []
        for (d, p, n), v in self._cookies.items():
            if d and host and d != host and not host.endswith("." + d.lstrip(".")):
                continue
            if path and p and not path.startswith(p.rstrip("/") + "/") and path != p:
                # basic path matching
                continue
            pairs.append(f"{n}={v}")
        return "; ".join(pairs)

    def __iter__(self):
        for (d, p, n), v in self._cookies.items():
            yield (n, v, d, p)

    def __len__(self):
        return len(self._cookies)