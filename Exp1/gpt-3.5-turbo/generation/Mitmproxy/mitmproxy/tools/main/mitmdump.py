import sys
from mitmproxy.tools.cmdline import mitmdump as cmdline
from mitmproxy.tools.dump import DumpMaster


def mitmdump(args=None):
    options = cmdline.parse_args(args)
    master = DumpMaster(vars(options))
    try:
        master.run()
    except KeyboardInterrupt:
        master.shutdown()
        return 0
    return 0


def main():
    sys.exit(mitmdump(sys.argv[1:]))


if __name__ == "__main__":
    main()