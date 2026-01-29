"""
Simplified `requests.Session` implementation relying on urllib.
"""

from __future__ import annotations

import base64
import json as _json
import urllib.request
import urllib.error
import http.cookiejar
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

from .models import Request, Response
from .exceptions import ConnectionError, Timeout, TooManyRedirects
from .auth import AuthBase, HTTPBasicAuth
from .utils import urlencode_params


class Session:
    """
    A **very** small subset of `requests.Session`.
    """

    def __init__(self):
        self.headers: Dict[str, str] = {
            "User-Agent": f"mini-requests/0.1"
        }
        self.auth: Optional[AuthBase | Tuple[str, str]] = None
        self.cookies = http.cookiejar.CookieJar()

        # opener that will manage cookies & redirects just like standard
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies),
            urllib.request.HTTPRedirectHandler(),
        )

    # --------------------------------------------------------------------- #
    # Internals                                                             #
    # --------------------------------------------------------------------- #
    def _merge_cookies(self, req: urllib.request.Request):
        # cookies are handled automatically by cookie processor; nothing to do.
        return req

    # --------------------------------------------------------------------- #
    # High-level API                                                        #
    # --------------------------------------------------------------------- #
    def request(
        self,
        method: str,
        url: str,
        *,
        params: Any = None,
        data: Any = None,
        json: Any = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float | Tuple[float, float]] = None,
        allow_redirects: bool = True,
        auth: Optional[AuthBase | Tuple[str, str]] = None,
        **kwargs,
    ) -> Response:

        method = method.upper()

        # --- Build URL with query parameters ------------------------------
        if params:
            query = urlencode(params, doseq=True)
            # Merge with existing
            url_parts = list(urlparse(url))
            if url_parts[4]:
                # existing query
                url_parts[4] = "&".join([url_parts[4], query])
            else:
                url_parts[4] = query
            url = urlunparse(url_parts)

        # --- Prepare body and Content-Type --------------------------------
        body = None
        actual_headers: Dict[str, str] = self.headers.copy()
        if headers:
            actual_headers.update(headers)

        if json is not None:
            body = _json.dumps(json).encode()
            actual_headers.setdefault("Content-Type", "application/json")
        elif data is not None:
            if isinstance(data, (dict, list, tuple)):
                body = urlencode(data, doseq=True).encode()
                actual_headers.setdefault(
                    "Content-Type", "application/x-www-form-urlencoded"
                )
            else:
                # assume bytes/str
                if isinstance(data, str):
                    body = data.encode()
                else:
                    body = data

        # --- Authentication ----------------------------------------------
        effective_auth = auth or self.auth
        if effective_auth is not None:
            if isinstance(effective_auth, tuple):
                effective_auth = HTTPBasicAuth(*effective_auth)
            if isinstance(effective_auth, AuthBase):
                dummy_req = Request(method, url, headers=actual_headers.copy())
                effective_auth(dummy_req)
                actual_headers.update(dummy_req.headers)

        # --- Build urllib request ----------------------------------------
        req = urllib.request.Request(
            url=url,
            data=body,
            headers=actual_headers,
            method=method,
        )

        # --- Perform request ---------------------------------------------
        try:
            resp: urllib.response.addinfourl = self._opener.open(req, timeout=timeout)
            # Read body
            content = resp.read()
            headers_dict = dict(resp.headers.items())
            response = Response(
                url=resp.geturl(),
                status_code=resp.getcode(),
                headers=headers_dict,
                content=content,
            )
            response.request = Request(method, url, headers=actual_headers, body=body)
            return response
        except urllib.error.HTTPError as e:
            # Even for HTTP errors (status >=400) urllib raises HTTPError.
            # We want to return a Response object to mimic 'requests' behaviour.
            content = e.read()
            headers_dict = dict(e.headers.items())
            response = Response(
                url=e.geturl(),
                status_code=e.code,
                headers=headers_dict,
                content=content,
            )
            response.request = Request(method, url, headers=actual_headers, body=body)
            # In requests, .request() returns Response even for errors.
            return response
        except urllib.error.URLError as e:
            if isinstance(e.reason, TimeoutError):
                raise Timeout(str(e)) from None
            raise ConnectionError(str(e)) from None

    # --------------------------------------------------------------------- #
    # Convenience HTTP verbs                                                #
    # --------------------------------------------------------------------- #
    def get(self, url: str, **kwargs):
        kwargs.setdefault("allow_redirects", True)
        return self.request("GET", url, **kwargs)

    def options(self, url: str, **kwargs):
        kwargs.setdefault("allow_redirects", True)
        return self.request("OPTIONS", url, **kwargs)

    def head(self, url: str, **kwargs):
        kwargs.setdefault("allow_redirects", False)
        return self.request("HEAD", url, **kwargs)

    def post(self, url: str, data=None, json=None, **kwargs):
        return self.request("POST", url, data=data, json=json, **kwargs)

    def put(self, url: str, data=None, **kwargs):
        return self.request("PUT", url, data=data, **kwargs)

    def patch(self, url: str, data=None, **kwargs):
        return self.request("PATCH", url, data=data, **kwargs)

    def delete(self, url: str, **kwargs):
        return self.request("DELETE", url, **kwargs)

    # --------------------------------------------------------------------- #
    # Context manager                                                       #
    # --------------------------------------------------------------------- #
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self):
        # Close any underlying connections (not strictly needed in urllib)
        pass