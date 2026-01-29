from mitmproxy.master import Master
from mitmproxy.options import Options

class DumpMaster(Master):
    def __init__(
        self,
        options: Options,
        with_termlog: bool = True,
        with_dumper: bool = True,
    ):
        super().__init__(options)
        # In a real implementation, we would add the TermLog and Dumper addons here.
        # For this subset, we just initialize the base Master.