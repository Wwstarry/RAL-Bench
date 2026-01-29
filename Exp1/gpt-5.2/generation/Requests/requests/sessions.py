from urllib.parse import urlsplit, urljoin

from .adapters import HTTPAdapter
from .cookies import RequestsCookieJar
from .exceptions import TooManyRedirects
from .models import Request, PreparedRequest, CaseInsensitiveDict


DEFAULT_REDIRECT_LIMIT = 30


class Session:
    def __init__(self):
        self.headers = CaseInsensitiveDict(
            {
                "User-Agent": "mini-requests/0.1",
                "Accept": "*/*",
                "Connection": "close",
            }
        )
        self.auth = None
        self.cookies = RequestsCookieJar()
        self.adapters = {"http://": HTTPAdapter(), "https://": HTTPAdapter()}
        self.max_redirects = DEFAULT_REDIRECT_LIMIT

    def mount(self, prefix, adapter):
        self.adapters[prefix] = adapter

    def get_adapter(self, url):
        for prefix, adapter in sorted(self.adapters.items(), key=lambda x: len(x[0]), reverse=True):
            if url.startswith(prefix):
                return adapter
        return None

    def prepare_request(self, request):
        if isinstance(request, PreparedRequest):
            return request
        if not isinstance(request, Request):
            raise TypeError("request must be a Request or PreparedRequest")
        # merge session headers
        headers = CaseInsensitiveDict(self.headers)
        headers.update(request.headers or {})
        # auth precedence: request.auth else session.auth
        auth = request.auth if request.auth is not None else self.auth
        # cookies: if request.cookies provided as dict, include; also session cookie jar handled later
        preq = PreparedRequest()
        preq.prepare(
            method=request.method,
            url=request.url,
            headers=headers,
            files=request.files,
            data=request.data,
            params=request.params,
            auth=auth,
            cookies=request.cookies,
            json=request.json,
        )
        return preq

    def request(
        self,
        method,
        url,
        params=None,
        data=None,
        headers=None,
        cookies=None,
        files=None,
        auth=None,
        timeout=None,
        allow_redirects=True,
        proxies=None,
        hooks=None,
        stream=False,
        verify=True,
        cert=None,
        json=None,
    ):
        req = Request(
            method=method,
            url=url,
            headers=headers,
            files=files,
            data=data,
            params=params,
            auth=auth,
            cookies=cookies,
            json=json,
        )
        preq = self.prepare_request(req)

        # add session cookies
        parts = urlsplit(preq.url)
        host = parts.hostname or ""
        path = parts.path or "/"
        cookie_header = self.cookies.cookie_header_for(host, path)
        if cookie_header:
            existing = preq.headers.get("cookie")
            preq.headers["Cookie"] = (existing + "; " if existing else "") + cookie_header

        resp = self.send(
            preq,
            timeout=timeout,
            allow_redirects=allow_redirects,
            proxies=proxies,
            stream=stream,
            verify=verify,
            cert=cert,
        )
        return resp

    def send(
        self,
        request,
        timeout=None,
        allow_redirects=True,
        proxies=None,
        stream=False,
        verify=True,
        cert=None,
    ):
        adapter = self.get_adapter(request.url)
        if adapter is None:
            from .exceptions import InvalidSchema

            raise InvalidSchema(f"No connection adapters were found for '{request.url}'")
        resp = adapter.send(
            request,
            timeout=timeout,
            allow_redirects=allow_redirects,
            stream=stream,
            verify=verify,
            cert=cert,
            proxies=proxies,
        )

        # update cookies from response
        set_cookie = None
        # http.client returns combined headers; our CaseInsensitiveDict stores last one.
        # handle both single and multiple by checking raw access isn't possible; best effort:
        sc = resp.headers.get("set-cookie")
        if sc:
            set_cookie = [sc]
        parts = urlsplit(resp.url)
        self.cookies.update_from_set_cookie_headers(set_cookie, parts.hostname or "")

        if allow_redirects:
            resp = self.resolve_redirects(resp, request, timeout=timeout, proxies=proxies, stream=stream, verify=verify, cert=cert)
        return resp

    def resolve_redirects(self, resp, req, timeout=None, proxies=None, stream=False, verify=True, cert=None):
        history = []
        cur = resp
        redirects = 0
        while cur.status_code in (301, 302, 303, 307, 308):
            redirects += 1
            if redirects > self.max_redirects:
                raise TooManyRedirects("Exceeded max redirects")
            loc = cur.headers.get("location")
            if not loc:
                break
            history.append(cur)
            new_url = urljoin(cur.url, loc)

            new_method = req.method
            new_body = req.body
            # Per common behavior: 303 -> GET, 302/301 for POST -> GET
            if cur.status_code == 303:
                new_method = "GET"
                new_body = None
            elif cur.status_code in (301, 302) and req.method in ("POST",):
                new_method = "GET"
                new_body = None

            new_req = PreparedRequest()
            new_req.method = new_method
            new_req.url = new_url
            new_req.headers = CaseInsensitiveDict(req.headers)
            new_req.body = new_body

            # refresh Host header
            parts = urlsplit(new_url)
            if parts.hostname:
                new_req.headers["Host"] = parts.hostname

            # attach cookies for new url
            cookie_header = self.cookies.cookie_header_for(parts.hostname or "", parts.path or "/")
            if cookie_header:
                new_req.headers["Cookie"] = cookie_header

            cur = self.get_adapter(new_url).send(
                new_req,
                timeout=timeout,
                allow_redirects=False,
                stream=stream,
                verify=verify,
                cert=cert,
                proxies=proxies,
            )

            sc = cur.headers.get("set-cookie")
            if sc:
                self.cookies.update_from_set_cookie_headers([sc], parts.hostname or "")

            req = new_req

        cur.history = history
        return cur

    def close(self):
        for a in set(self.adapters.values()):
            try:
                a.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False