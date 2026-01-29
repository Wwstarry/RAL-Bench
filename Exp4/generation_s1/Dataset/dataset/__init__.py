from __future__ import annotations

from .database import Database


def connect(url: str) -> Database:
    """Connect to a database URL.

    Supported URLs:
      - sqlite:///:memory:
      - sqlite:////absolute/path.db
      - sqlite:///relative/path.db
    """
    return Database(url)


__all__ = ["connect", "Database"]