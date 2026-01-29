from .cmdline import mitmdump
from .dump import DumpMaster

def mitmdump_entry():
    parser = mitmdump()
    args = parser.parse_args()
    master = DumpMaster(args)
    master.run()