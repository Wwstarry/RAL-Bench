"""A tiny, file-based JSON document database.

This repository provides a minimal subset of the TinyDB-like API tailored to the
contract in the task description.
"""

from .database import TinyDB
from .storages import JSONStorage
from .queries import Query, where
from .table import Document

__all__ = ["TinyDB", "JSONStorage", "Query", "where", "Document"]