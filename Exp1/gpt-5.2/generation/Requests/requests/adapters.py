import http.client
import socket
from urllib.parse import urlsplit

from .exceptions import ConnectionError, Timeout
from .models import Response, CaseInsensitiveDict


class HTTPAdapter:
    def __init__(self):
        pass

    def close(self):
        pass

    def send(
        self,
        request,
        timeout=None,
        allow_redirects=True,
        stream=False,
        verify=True,
        cert=None,
        proxies=None,
    ):
        parts = urlsplit(request.url)
        scheme = parts.scheme
        host = parts.hostname
        port = parts.port
        if port is None:
            port = 443 if scheme == "https" else 80
        path = parts.path or "/"
        if parts.query:
            path = f"{path}?{parts.query}"

        headers = dict(request.headers.items())
        if "host" not in headers:
            headers["Host"] = host

        conn_cls = http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection

        conn = None
        try:
            # timeout can be float or (connect, read); we use max if tuple
            t = timeout
            if isinstance(timeout, (tuple, list)) and timeout:
                t = max([x for x in timeout if x is not None] or [None])
            conn = conn_cls(host, port, timeout=t)
            conn.request(request.method, path, body=request.body, headers=headers)
            resp = conn.getresponse()

            r = Response()
            r.status_code = resp.status
            r.reason = resp.reason
            r.url = request.url
            r.request = request
            r.headers = CaseInsensitiveDict({k: v for k, v in resp.getheaders()})

            if stream:
                # minimal: still read now; streaming not implemented
                r._content = resp.read()
            else:
                r._content = resp.read()

            return r
        except socket.timeout as e:
            raise Timeout(str(e)) from e
        except OSError as e:
            raise ConnectionError(str(e)) from e
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass