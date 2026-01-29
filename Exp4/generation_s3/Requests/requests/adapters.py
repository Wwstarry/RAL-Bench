from __future__ import annotations

import http.client
import socket
from urllib.parse import urlsplit

from .exceptions import ConnectionError, InvalidSchema
from .models import Response
from .structures import CaseInsensitiveDict


class HTTPAdapter:
    def send(self, request, timeout=None, stream=False, verify=None):
        split = urlsplit(request.url)
        scheme = split.scheme.lower()
        if scheme not in ("http", "https"):
            raise InvalidSchema(f"Unsupported scheme: {scheme}")

        host = split.hostname
        if not host:
            raise ConnectionError("No host specified")

        port = split.port
        path = split.path or "/"
        if split.query:
            path = f"{path}?{split.query}"

        # headers: must be plain dict for http.client
        headers = dict(CaseInsensitiveDict(request.headers).items())
        body = request.body
        if body is not None and "Content-Length" not in CaseInsensitiveDict(headers):
            headers["Content-Length"] = str(len(body))

        # Basic connection selection
        try:
            if scheme == "https":
                conn = http.client.HTTPSConnection(host, port or 443, timeout=_timeout_value(timeout))
            else:
                conn = http.client.HTTPConnection(host, port or 80, timeout=_timeout_value(timeout))
            conn.request(request.method, path, body=body, headers=headers)
            resp = conn.getresponse()

            r = Response()
            r.status_code = resp.status
            r.reason = resp.reason
            r.url = request.url
            r.headers = CaseInsensitiveDict({k: v for k, v in resp.getheaders()})
            if not stream:
                r.content = resp.read() or b""
            else:
                # minimal: still read eagerly (stream accepted but not implemented)
                r.content = resp.read() or b""
            return r
        except (OSError, http.client.HTTPException, socket.error) as e:
            raise ConnectionError(str(e)) from e
        finally:
            try:
                conn.close()
            except Exception:
                pass


def _timeout_value(timeout):
    if timeout is None:
        return None
    if isinstance(timeout, (tuple, list)) and timeout:
        # http.client uses a single timeout; prefer read timeout if provided
        try:
            return float(timeout[-1])
        except Exception:
            return None
    try:
        return float(timeout)
    except Exception:
        return None