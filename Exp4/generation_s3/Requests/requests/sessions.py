from __future__ import annotations

from urllib.parse import urlsplit, urljoin

from .adapters import HTTPAdapter
from .auth import HTTPBasicAuth
from .cookies import RequestsCookieJar, merge_cookies, cookiejar_from_dict
from .exceptions import (
    URLRequired,
    MissingSchema,
    InvalidSchema,
    TooManyRedirects,
)
from .models import Request, Response, PreparedRequest
from .structures import CaseInsensitiveDict


REDIRECT_STATUSES = {301, 302, 303, 307, 308}


class Session:
    def __init__(self):
        self.headers = {}
        self.cookies = RequestsCookieJar()
        self.auth = None
        self.adapters = {
            "http://": HTTPAdapter(),
            "https://": HTTPAdapter(),
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def close(self):
        # no persistent connections in this minimal adapter
        return None

    def mount(self, prefix: str, adapter):
        self.adapters[prefix] = adapter

    def request(self, method, url, **kwargs) -> Response:
        if url is None or url == "":
            raise URLRequired("A valid URL is required")
        if "://" not in str(url):
            raise MissingSchema("Invalid URL: No scheme supplied. Perhaps you meant http://...")

        split = urlsplit(url)
        scheme = split.scheme.lower()
        if scheme not in ("http", "https"):
            raise InvalidSchema(f"No connection adapters were found for '{scheme}://'")

        params = kwargs.get("params", None)
        data = kwargs.get("data", None)
        json = kwargs.get("json", None)
        headers = kwargs.get("headers", None) or {}
        cookies = kwargs.get("cookies", None)
        auth = kwargs.get("auth", None)
        timeout = kwargs.get("timeout", None)
        allow_redirects = kwargs.get("allow_redirects", None)
        stream = kwargs.get("stream", False)
        verify = kwargs.get("verify", None)
        # hooks accepted but ignored
        _ = kwargs.get("hooks", None)

        if allow_redirects is None:
            allow_redirects = method.upper() in ("GET", "OPTIONS")

        # Merge headers: session.headers then request headers override
        merged_headers = CaseInsensitiveDict(self.headers)
        merged_headers.update(headers)

        # Merge cookies: session jar + request cookies for this call
        merged_cookiejar = merge_cookies(self.cookies, cookies)

        # Build Request and prepare
        req = Request(
            method=method,
            url=url,
            headers=dict(merged_headers.items()),
            data=data,
            params=params,
            auth=auth,
            cookies=merged_cookiejar,
            json=json,
        )
        prep = req.prepare()

        # Attach Cookie header
        cookie_header = merged_cookiejar.get_cookie_header() if isinstance(merged_cookiejar, RequestsCookieJar) else None
        if cookie_header and prep.headers.get("Cookie") is None:
            prep.headers["Cookie"] = cookie_header

        # Apply auth: request auth, else session auth
        effective_auth = auth if auth is not None else self.auth
        if isinstance(effective_auth, tuple) and len(effective_auth) == 2:
            effective_auth = HTTPBasicAuth(effective_auth[0], effective_auth[1])
        if callable(effective_auth):
            prep = effective_auth(prep) or prep

        # Send with redirects
        resp = self._send(prep, timeout=timeout, stream=stream, verify=verify)
        resp.request = prep

        # cookies from response -> response.cookies and session.cookies
        self._extract_and_store_cookies(resp)

        if allow_redirects and resp.status_code in REDIRECT_STATUSES:
            return self._resolve_redirects(
                resp,
                prep,
                timeout=timeout,
                stream=stream,
                verify=verify,
                max_redirects=kwargs.get("max_redirects", 30),
            )

        return resp

    def _adapter_for_url(self, url: str):
        # Longest prefix match.
        best = None
        for prefix, adapter in self.adapters.items():
            if url.startswith(prefix):
                if best is None or len(prefix) > len(best[0]):
                    best = (prefix, adapter)
        if best is None:
            raise InvalidSchema("No connection adapters were found")
        return best[1]

    def _send(self, prep: PreparedRequest, timeout=None, stream=False, verify=None) -> Response:
        adapter = self._adapter_for_url(prep.url)
        r = adapter.send(prep, timeout=timeout, stream=stream, verify=verify)
        return r

    def _extract_and_store_cookies(self, resp: Response):
        # Ensure response.cookies exists
        jar = RequestsCookieJar()
        # Try multiple Set-Cookie headers if provided in combined form
        set_cookie = resp.headers.get("Set-Cookie")
        if set_cookie:
            # Could be multiple cookies in one header; SimpleCookie handles it often.
            jar.update_from_set_cookie_headers(set_cookie)
        resp.cookies = jar
        # Update session cookies
        if jar:
            self.cookies.update(jar)

    def _resolve_redirects(self, resp: Response, prep: PreparedRequest, timeout=None, stream=False, verify=None, max_redirects=30):
        history = []
        current_resp = resp
        current_prep = prep

        for _i in range(int(max_redirects)):
            if current_resp.status_code not in REDIRECT_STATUSES:
                break

            location = current_resp.headers.get("Location")
            if not location:
                break

            history.append(current_resp)

            next_url = urljoin(current_resp.url, location)

            # Per RFC/requests-like behavior:
            method = current_prep.method
            body = current_prep.body
            headers = CaseInsensitiveDict(current_prep.headers)

            if current_resp.status_code in (301, 302, 303):
                if method not in ("GET", "HEAD"):
                    method = "GET"
                    body = None
                    # Remove content headers when switching to GET
                    for h in ("Content-Length", "Content-Type"):
                        if h in headers:
                            del headers[h]

            next_prep = PreparedRequest()
            next_prep.prepare(
                method=method,
                url=next_url,
                headers=dict(headers.items()),
                data=None,
                params=None,
                json=None,
                cookies=None,
                auth=None,
            )
            next_prep.body = body

            # Ensure cookies carried forward
            cookie_header = self.cookies.get_cookie_header()
            if cookie_header and next_prep.headers.get("Cookie") is None:
                next_prep.headers["Cookie"] = cookie_header

            # Re-apply session auth (do not reuse per-request auth if it was provided; minimal behavior)
            effective_auth = self.auth
            if isinstance(effective_auth, tuple) and len(effective_auth) == 2:
                effective_auth = HTTPBasicAuth(effective_auth[0], effective_auth[1])
            if callable(effective_auth):
                next_prep = effective_auth(next_prep) or next_prep

            next_resp = self._send(next_prep, timeout=timeout, stream=stream, verify=verify)
            next_resp.request = next_prep
            self._extract_and_store_cookies(next_resp)

            current_resp = next_resp
            current_prep = next_prep

        else:
            raise TooManyRedirects(f"Exceeded {max_redirects} redirects")

        current_resp.history = history
        return current_resp

    # Convenience methods
    def get(self, url, params=None, **kwargs):
        kwargs.setdefault("allow_redirects", True)
        return self.request("GET", url, params=params, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self.request("POST", url, data=data, json=json, **kwargs)

    def put(self, url, data=None, **kwargs):
        return self.request("PUT", url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)

    def head(self, url, **kwargs):
        kwargs.setdefault("allow_redirects", False)
        return self.request("HEAD", url, **kwargs)

    def options(self, url, **kwargs):
        kwargs.setdefault("allow_redirects", True)
        return self.request("OPTIONS", url, **kwargs)

    def patch(self, url, data=None, **kwargs):
        return self.request("PATCH", url, data=data, **kwargs)


def session():
    return Session()