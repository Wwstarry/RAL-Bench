import typing
from mitmproxy import exceptions

if typing.TYPE_CHECKING:
    from mitmproxy.master import Master

class Loader:
    """
    A loader object is passed to the load() method of addons.
    """
    def __init__(self, master: "Master"):
        self.master = master

    def add_option(self, name: str, typespec: type, default: typing.Any, help: str) -> None:
        self.master.options.add_option(name, typespec, default, help)

class AddonManager:
    def __init__(self, master: "Master"):
        self.master = master
        self.lookup = {}
        self.chain = []

    def register(self, addon):
        name = getattr(addon, "name", str(type(addon).__name__))
        self.lookup[name] = addon
        self.chain.append(addon)
        if hasattr(addon, "load"):
            addon.load(Loader(self.master))

    def add(self, *addons):
        for a in addons:
            self.register(a)

    def remove(self, addon):
        if addon in self.chain:
            self.chain.remove(addon)

    def trigger(self, event_name: str, *args, **kwargs):
        for addon in self.chain:
            func = getattr(addon, event_name, None)
            if func:
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    print(f"Addon error in {event_name}: {e}")

    def __len__(self):
        return len(self.chain)

    def __iter__(self):
        return iter(self.chain)