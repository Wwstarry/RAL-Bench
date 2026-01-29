from types import SimpleNamespace

# These must be importable and mutable, and safe at import time.
cmdLineOptions = None

# Runtime configuration and knowledge-base namespaces.
conf = SimpleNamespace()
kb = SimpleNamespace()