"""
Stegano – A simple pure-python steganography library.

The goal of this package is to provide a subset of the API of the original
`Stegano` project (https://github.com/cedricbonhomme/Stegano) that is sufficient
for educational and testing purposes.

Only a handful of hiding techniques are implemented, but the public API of the
sub-modules tries to stay compatible with the reference implementation so that
3rd-party code and existing tutorials continue to work.
"""
from importlib import import_module
from types import ModuleType
from typing import Any

# Lazy sub-module loader to avoid importing Pillow / wave unless necessary.
def _lazy_import(name: str) -> ModuleType:
    module: ModuleType = import_module(name)
    globals()[name.rpartition(".")[2]] = module  # re-export
    return module


def __getattr__(attr: str) -> Any:  # pragma: no cover
    if attr in ("lsb", "red", "exifHeader", "wav"):
        return _lazy_import(f"stegano.{attr}")
    raise AttributeError(attr)