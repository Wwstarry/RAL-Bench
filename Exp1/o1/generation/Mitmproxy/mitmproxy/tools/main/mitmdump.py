"""
Minimal mitmdump CLI entrypoint for testing.
"""

def mitmdump():
    """
    Main entry point for the mitmdump tool (placeholder).
    """
    from mitmproxy.tools.cmdline.mitmdump import create_parser

    parser = create_parser()
    args = parser.parse_args()
    if args.version:
        print("mitmdump version 0.0.1 (minimal placeholder)")
    else:
        parser.print_help()