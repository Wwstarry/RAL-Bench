import os
import sys
import textwrap
from pathlib import Path

import pytest


TARGET_ENV = "REQUESTS_TARGET"
ROOT_DIR = Path(__file__).resolve().parents[2]


def _looks_like_repo_root(repo_root: Path) -> bool:
    return (repo_root / "requests" / "__init__.py").exists()


def _select_repo_root() -> Path:
    override = os.environ.get("RACB_REPO_ROOT")
    if override:
        p = Path(override).resolve()
        if _looks_like_repo_root(p):
            return p

    target = os.environ.get(TARGET_ENV, "generated").lower()
    if target == "reference":
        return (ROOT_DIR / "repositories" / "requests").resolve()

    return (ROOT_DIR / "generation" / "Requests").resolve()


REPO_ROOT = _select_repo_root()
repo_str = str(REPO_ROOT)
if repo_str not in sys.path:
    sys.path.insert(0, repo_str)

import requests  # noqa: E402
from requests import exceptions as req_exc  # noqa: E402


def test_imports_core_modules() -> None:
    import requests.api  # noqa: F401
    import requests.sessions  # noqa: F401
    import requests.models  # noqa: F401
    import requests.auth  # noqa: F401
    import requests.exceptions  # noqa: F401

    assert hasattr(requests, "get")
    assert hasattr(requests, "Session")


def test_invalid_url_raises_request_exception() -> None:
    with pytest.raises(req_exc.RequestException):
        requests.get("not a url")


def test_missing_schema_raises_cleanly() -> None:
    with pytest.raises(req_exc.MissingSchema):
        requests.get("example.com/path")


def test_response_json_on_non_json_fails_safely() -> None:
    r = requests.Response()
    r._content = b"plain text"
    r.status_code = 200
    r.headers["Content-Type"] = "text/plain"
    with pytest.raises(ValueError):
        _ = r.json()


def test_session_close_is_safe_to_call_multiple_times() -> None:
    s = requests.Session()
    s.close()
    s.close()
    assert True
