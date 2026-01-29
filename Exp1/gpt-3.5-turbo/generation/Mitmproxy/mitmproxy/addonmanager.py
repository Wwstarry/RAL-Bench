from typing import List, Callable


class AddonManager:
    def __init__(self):
        self.addons = []
        self.options = {}
        self.commands = {}

    def add(self, addon):
        self.addons.append(addon)

    def configure(self, options: dict):
        self.options.update(options)
        for addon in self.addons:
            if hasattr(addon, "configure"):
                addon.configure(options)

    def command(self, name: str, func: Callable):
        self.commands[name] = func

    def run_command(self, name: str, *args, **kwargs):
        if name in self.commands:
            return self.commands[name](*args, **kwargs)
        raise ValueError(f"Command {name} not found")