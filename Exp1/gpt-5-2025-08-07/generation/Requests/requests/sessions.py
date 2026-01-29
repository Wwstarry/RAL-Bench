import http.client
import socket
import ssl
from urllib.parse import urlsplit, urlunsplit, urljoin
from .models import Request, PreparedRequest, Response
from .utils import CaseInsensitiveDict, merge_setting, merge_cookies
from .exceptions import (
    ConnectionError,
    Timeout,
    TooManyRedirects,
    InvalidURL,
)
from .auth import HTTPBasicAuth
from .cookies import RequestsCookieJar


DEFAULT_HEADERS = CaseInsensitiveDict(
    {
        "User-Agent": "python-requests-lite/1.0",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }
)


class Session:
    def __init__(self):
        self.headers = CaseInsensitiveDict(DEFAULT_HEADERS.to_dict())
        self.auth = None
        self.cookies = RequestsCookieJar()
        self.max_redirects = 30

    def prepare_request(self, request):
        if not isinstance(request, Request):
            raise ValueError("prepare_request expects a Request")
        # Merge headers
        headers = CaseInsensitiveDict(self.headers.to_dict())
        if request.headers:
            for k, v in request.headers.items():
                headers[k] = v

        # Merge cookies: session + request
        merged_cookies = merge_cookies(self.cookies.get_dict() if self.cookies else {}, request.cookies or {})
        # Prepare
        p = PreparedRequest()
        p.prepare(
            method=request.method,
            url=request.url,
            headers=headers.to_dict(),
            files=request.files,
            data=request.data,
            json=request.json,
            params=request.params,
            auth=merge_setting(request.auth, self.auth),
            cookies=merged_cookies,
        )
        # If auth is a tuple and not applied yet (no Authorization header), apply now
        if (request.auth or self.auth) and "Authorization" not in p.headers:
            auth = request.auth if request.auth is not None else self.auth
            if isinstance(auth, tuple) and len(auth) == 2:
                HTTPBasicAuth(*auth)(p)
            elif hasattr(auth, "__call__"):
                auth(p)
        return p

    def request(
        self,
        method,
        url,
        params=None,
        data=None,
        json=None,
        headers=None,
        cookies=None,
        files=None,
        auth=None,
        timeout=None,
        allow_redirects=True,
    ):
        req = Request(method=method, url=url)
        req.headers = headers or {}
        req.files = files
        req.data = data
        req.json = json
        req.params = params
        req.auth = auth
        req.cookies = cookies

        prep = self.prepare_request(req)
        resp = self.send(prep, timeout=timeout, allow_redirects=allow_redirects)
        return resp

    def get(self, url, **kwargs):
        kwargs.setdefault("allow_redirects", True)
        return self.request("GET", url, **kwargs)

    def options(self, url, **kwargs):
        kwargs.setdefault("allow_redirects", True)
        return self.request("OPTIONS", url, **kwargs)

    def head(self, url, **kwargs):
        kwargs.setdefault("allow_redirects", False)
        return self.request("HEAD", url, **kwargs)

    def post(self, url, **kwargs):
        kwargs.setdefault("allow_redirects", True)
        return self.request("POST", url, **kwargs)

    def put(self, url, **kwargs):
        kwargs.setdefault("allow_redirects", True)
        return self.request("PUT", url, **kwargs)

    def patch(self, url, **kwargs):
        kwargs.setdefault("allow_redirects", True)
        return self.request("PATCH", url, **kwargs)

    def delete(self, url, **kwargs):
        kwargs.setdefault("allow_redirects", True)
        return self.request("DELETE", url, **kwargs)

    def send(self, request, timeout=None, allow_redirects=True):
        if not isinstance(request, PreparedRequest):
            raise ValueError("send expects PreparedRequest")
        history = []
        req = request
        redirects_remaining = self.max_redirects
        while True:
            resp = self._send_once(req, timeout=timeout)
            resp.request = req
            # Manage cookies from response
            self._extract_cookies(resp)
            # Handle redirects
            if allow_redirects and resp.status_code in (301, 302, 303, 307, 308):
                if "Location" not in resp.headers:
                    return resp
                if redirects_remaining <= 0:
                    raise TooManyRedirects("Exceeded maximum redirects", response=resp, request=req)
                redirects_remaining -= 1
                location = resp.headers["Location"]
                new_url = urljoin(resp.url, location)
                new_method = req.method
                new_body = req.body
                new_headers = CaseInsensitiveDict(req.headers.to_dict() if isinstance(req.headers, CaseInsensitiveDict) else dict(req.headers))
                # Adjust method per RFC: 303 -> GET; 301/302 -> GET for non-HEAD
                if resp.status_code == 303:
                    new_method = "GET"
                    new_body = None
                    # Remove content headers
                    for h in ["Content-Length", "Content-Type"]:
                        if h in new_headers:
                            del new_headers[h]
                elif resp.status_code in (301, 302):
                    if req.method not in ("GET", "HEAD"):
                        new_method = "GET"
                        new_body = None
                        for h in ["Content-Length", "Content-Type"]:
                            if h in new_headers:
                                del new_headers[h]
                # On cross-domain, Authorization header shouldn't be forwarded
                old_host = urlsplit(req.url).netloc
                new_host = urlsplit(new_url).netloc
                if old_host != new_host and "Authorization" in new_headers:
                    del new_headers["Authorization"]
                # Build new PreparedRequest
                new_req = PreparedRequest()
                new_req.prepare(
                    method=new_method,
                    url=new_url,
                    headers=new_headers.to_dict() if isinstance(new_headers, CaseInsensitiveDict) else dict(new_headers),
                    data=new_body,
                    json=None,
                    params=None,
                    auth=None,
                    cookies=self.cookies.get_dict(),
                )
                history.append(resp)
                req = new_req
                continue
            # attach history
            resp.history = history
            return resp

    def _send_once(self, prep, timeout=None):
        # Build connection
        try:
            parts = urlsplit(prep.url)
        except Exception as e:
            raise InvalidURL(str(e), request=prep)
        scheme = parts.scheme or "http"
        host = parts.hostname
        port = parts.port
        path = parts.path or "/"
        if parts.query:
            path = path + "?" + parts.query
        if host is None:
            raise InvalidURL("Invalid URL", request=prep)
        # Ensure Host header
        if "Host" not in prep.headers:
            if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
                prep.headers["Host"] = f"{host}:{port}"
            else:
                prep.headers["Host"] = host
        # Add cookies from session if not set explicitly
        if "Cookie" not in prep.headers:
            ck = self.cookies.get_dict()
            if ck:
                cookie_header = "; ".join([f"{k}={v}" for k, v in ck.items()])
                prep.headers["Cookie"] = cookie_header
        # Establish connection
        conn = None
        try:
            if scheme == "http":
                conn = http.client.HTTPConnection(host, port or 80, timeout=timeout)
            elif scheme == "https":
                # default context
                context = ssl.create_default_context()
                conn = http.client.HTTPSConnection(host, port or 443, timeout=timeout, context=context)
            else:
                raise InvalidURL(f"Unsupported scheme: {scheme}", request=prep)
            conn.request(prep.method, path, body=prep.body, headers=dict(prep.headers.items()))
            r = conn.getresponse()
            resp = Response()
            resp.status_code = r.status
            resp.reason = r.reason
            headers = CaseInsensitiveDict()
            for k, v in r.getheaders():
                # http.client folds duplicate headers; but Set-Cookie appears multiple times, getheaders returns all
                headers[k] = v
            resp.headers = headers
            body = b""
            # For HEAD we expect no body; but read anyway to free the connection
            try:
                body = r.read()
            except socket.timeout as e:
                conn.close()
                raise Timeout("Read timed out", request=prep)
            resp._content = body
            resp.url = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, parts.fragment))
            resp.encoding = None  # will be detected lazily
            return resp
        except socket.timeout as e:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
            raise Timeout("Connection timed out", request=prep) from e
        except (socket.gaierror, socket.error, http.client.HTTPException) as e:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
            raise ConnectionError(str(e), request=prep) from e
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _extract_cookies(self, response):
        """
        Very simple Set-Cookie parsing: name=value; ... (ignores attributes)
        Multiple Set-Cookie headers may be present.
        """
        from http.cookies import SimpleCookie
        jar = RequestsCookieJar()
        # http.client getheaders returns a list; but we already folded headers in dict
        # So we need raw headers. Workaround: check for 'Set-Cookie' or 'set-cookie' keys and split on comma if multiple
        # However commas may appear in Expires. SimpleCookie can parse combined string separated by commas poorly.
        # To better handle, rely on response received: http.client returns headers per line via msg.get_all in internal.
        # Since we can't access those easily now, attempt to parse header value potentially containing multiple cookies.
        set_cookie_value = response.headers.get("Set-Cookie") or response.headers.get("set-cookie")
        if set_cookie_value:
            # Try to split by \n or comma; first try naive SimpleCookie on whole string
            sc = SimpleCookie()
            try:
                sc.load(set_cookie_value)
            except Exception:
                # fallback split by comma (best-effort)
                for part in set_cookie_value.split(","):
                    try:
                        sc.load(part)
                    except Exception:
                        continue
            for morsel in sc.values():
                name = morsel.key
                value = morsel.value
                self.cookies.set(name, value)
                jar.set(name, value)
        response.cookies = jar

    def close(self):
        # nothing persistent to close in this lightweight implementation
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False