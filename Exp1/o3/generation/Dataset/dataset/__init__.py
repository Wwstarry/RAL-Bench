"""
Light-weight tabular data access layer.

Only the core public API that the test-suite requires is implemented.
"""
from urllib.parse import urlparse
import os

from .database import Database  # noqa: F401 (re-export)


def connect(url: str = "sqlite:///:memory:", **kwargs) -> Database:
    """
    Connect to a database and return a :class:`~dataset.database.Database`
    instance.

    Only sqlite URLs of the form ``sqlite:///path/to/file.db`` or
    ``sqlite:///:memory:`` are supported.
    """
    parsed = urlparse(url)
    if parsed.scheme != "sqlite":
        raise ValueError("This lightweight implementation only supports SQLite.")
    # sqlite:///file.db -> path is /file.db, strip leading slash
    if parsed.path in ("", "/"):
        # Fallback to in-memory if no explicit path
        database_path = ":memory:"
    else:
        # Special case for in-memory
        if parsed.path == "/:memory:" or parsed.netloc == ":memory:":
            database_path = ":memory:"
        else:
            # Ensure directories exist for on-disk sqlite files.
            database_path = os.path.expanduser(parsed.path.lstrip("/"))
            dirname = os.path.dirname(database_path)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname, exist_ok=True)

    return Database(database_path, **kwargs)