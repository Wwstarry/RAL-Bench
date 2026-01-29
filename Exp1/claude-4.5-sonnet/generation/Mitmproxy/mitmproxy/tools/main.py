"""
Main entry points for mitmproxy tools.
"""

import sys
from typing import Optional, List
from mitmproxy.tools import cmdline
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options
from mitmproxy import __version__


def mitmdump(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for mitmdump.
    """
    parser = cmdline.mitmdump()
    parsed_args = parser.parse_args(args)
    
    if parsed_args.version:
        print(f"mitmdump {__version__}")
        return 0
    
    # Build options from parsed arguments
    options_dict = {}
    
    if parsed_args.listen_host:
        options_dict["listen_host"] = parsed_args.listen_host
    if parsed_args.listen_port:
        options_dict["listen_port"] = parsed_args.listen_port
    if parsed_args.mode:
        options_dict["mode"] = parsed_args.mode
    if parsed_args.ssl_insecure:
        options_dict["ssl_insecure"] = parsed_args.ssl_insecure
    if parsed_args.certs:
        options_dict["certs"] = parsed_args.certs
    if parsed_args.showhost:
        options_dict["showhost"] = parsed_args.showhost
    if parsed_args.filter:
        options_dict["flow_filter"] = parsed_args.filter
    if parsed_args.save_stream_file:
        options_dict["save_stream_file"] = parsed_args.save_stream_file
    if parsed_args.scripts:
        options_dict["scripts"] = parsed_args.scripts
    if parsed_args.verbosity:
        options_dict["verbosity"] = parsed_args.verbosity
    
    options = Options(**options_dict)
    
    master = DumpMaster(options)
    
    try:
        master.run()
    except KeyboardInterrupt:
        pass
    finally:
        master.shutdown()
    
    return 0


def mitmproxy_console(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for mitmproxy (console UI).
    """
    parser = cmdline.mitmproxy()
    parsed_args = parser.parse_args(args)
    
    if parsed_args.version:
        print(f"mitmproxy {__version__}")
        return 0
    
    # For this minimal implementation, just print a message
    print("mitmproxy console UI not implemented in minimal version")
    return 0


def mitmweb(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for mitmweb.
    """
    parser = cmdline.mitmweb()
    parsed_args = parser.parse_args(args)
    
    if parsed_args.version:
        print(f"mitmweb {__version__}")
        return 0
    
    # For this minimal implementation, just print a message
    print("mitmweb not implemented in minimal version")
    return 0


if __name__ == "__main__":
    sys.exit(mitmdump())