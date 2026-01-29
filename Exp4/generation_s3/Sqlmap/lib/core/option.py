from types import SimpleNamespace

from lib.core import data


def _ensure_namespace(obj, name: str) -> SimpleNamespace:
    if obj is None:
        obj = SimpleNamespace()
    if not hasattr(obj, "__dict__"):
        # Fallback to a fresh namespace if some non-namespace was assigned.
        obj = SimpleNamespace()
    return obj


def initOptions(options) -> None:
    """
    Populate global cmdLineOptions and conf defaults based on parsed options.
    """
    data.cmdLineOptions = options
    data.conf = _ensure_namespace(getattr(data, "conf", None), "conf")
    data.kb = _ensure_namespace(getattr(data, "kb", None), "kb")

    # Copy a minimal set of parsed options into conf (sqlmap style).
    # Tests may read/write these attributes.
    for key in ("url", "data", "batch", "verbose"):
        if hasattr(options, key):
            setattr(data.conf, key, getattr(options, key))

    # Derived/extra defaults expected to exist in some integrations
    if not hasattr(data.conf, "target"):
        data.conf.target = None
    if not hasattr(data.conf, "threads"):
        data.conf.threads = 1


def init(options=None) -> None:
    """
    Ensure conf and kb exist and are initialized. Safe no-op if nothing provided.
    """
    data.conf = _ensure_namespace(getattr(data, "conf", None), "conf")
    data.kb = _ensure_namespace(getattr(data, "kb", None), "kb")

    if options is not None:
        data.cmdLineOptions = options
    elif data.cmdLineOptions is None:
        # Nothing to do, but keep safe invariants
        data.cmdLineOptions = None

    # Ensure a couple of kb flags exist
    if not hasattr(data.kb, "banner"):
        data.kb.banner = None
    if not hasattr(data.kb, "injectionTested"):
        data.kb.injectionTested = False