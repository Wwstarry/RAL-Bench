import sys

from lib.core.data import conf


def start():
    """
    Main controller entry point.

    This stub does not perform real testing; it just validates that a target is provided
    and exits deterministically.
    """
    url = getattr(conf, "url", None)
    data_str = getattr(conf, "data", None)

    if not url and not data_str:
        sys.stderr.write("No target provided. Use -u/--url and/or --data.\n")
        return 1

    # Deterministic, benign behavior
    if url:
        sys.stdout.write(f"Target: {url}\n")
    if data_str:
        sys.stdout.write("Data: (provided)\n")

    sys.stdout.write("NOTE: This is a stub implementation; no real SQL injection tests are performed.\n")
    return 0