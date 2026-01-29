# click/core.py

import sys


class Context:
    def __init__(self, command):
        self.command = command
        self.params = {}

    def invoke(self, callback, *args, **kwargs):
        return callback(*args, **kwargs)


class Command:
    def __init__(self, name, callback, params=None, help=None):
        self.name = name
        self.callback = callback
        self.params = params or []
        self.help = help

    def invoke(self, ctx, *args, **kwargs):
        return ctx.invoke(self.callback, *args, **kwargs)

    def get_help(self):
        return self.help or ""


class Group(Command):
    def __init__(self, name, help=None):
        super().__init__(name, callback=None, help=help)
        self.commands = {}

    def add_command(self, cmd):
        self.commands[cmd.name] = cmd

    def invoke(self, ctx, *args, **kwargs):
        raise RuntimeError("Cannot invoke a group directly.")

    def get_help(self):
        help_text = self.help or ""
        for cmd_name in self.commands:
            help_text += f"\n  {cmd_name}"
        return help_text