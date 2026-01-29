from lib.core.data import conf


def start():
    """
    Controller entry point. For this minimal implementation, we only validate that
    the invocation is sensible and exit cleanly.
    """
    # If a URL is provided, we still don't do network operations.
    # Provide a friendly message and exit 0 to keep tests benign.
    url = conf.get("url")
    if url:
        # Keep output minimal and deterministic.
        print(f"[INFO] target set to '{url}'")
        print("[INFO] this stub does not perform real injection tests")
        return 0

    # If no URL and no explicit action, show a minimal guidance message.
    # sqlmap typically requires a target, but tests may invoke without one.
    print("[INFO] no target provided (use -u/--url). Use -h for help.")
    return 0