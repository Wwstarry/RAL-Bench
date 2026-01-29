import os
import sys
import inspect
import argparse
from functools import update_wrapper
from .utils import echo, get_os_args

class Context:
    def __init__(self, command, parent=None, info_name=None, args=None, obj=None, **extra):
        self.command = command
        self.parent = parent
        self.info_name = info_name
        self.args = args or []
        self.obj = obj
        self.extra = extra
        self.protected_args = []
        self.params = {}
        self._close_objects = []

    def ensure_object(self, obj_type):
        if not self.obj:
            self.obj = obj_type()
        return self.obj

    def close(self):
        for obj in self._close_objects:
            obj.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class Parameter:
    def __init__(self, name=None, param_type=None, required=False, default=None, help=None, **kwargs):
        self.name = name
        self.type = param_type or str
        self.required = required
        self.default = default
        self.help = help
        self.expose_value = True

class Option(Parameter):
    def __init__(self, param_decls, **kwargs):
        super().__init__(**kwargs)
        self.param_decls = param_decls

class Argument(Parameter):
    def __init__(self, param_decls, **kwargs):
        super().__init__(**kwargs)
        self.param_decls = param_decls

class Command:
    def __init__(self, name, context_settings=None, callback=None, params=None, help=None, **attrs):
        self.name = name
        self.context_settings = context_settings or {}
        self.callback = callback
        self.params = params or []
        self.help = help
        self.attrs = attrs

    def parse_args(self, ctx, args):
        parser = self._create_parser(ctx)
        opts, args = parser.parse_known_args(args)
        return opts, args

    def invoke(self, ctx):
        if self.callback is not None:
            ctx.params.update(ctx.protected_args)
            return self.callback(**ctx.params)

    def main(self, args=None, **extra):
        try:
            with self.make_context(self.name, args, **extra) as ctx:
                return self.invoke(ctx)
        except Exit as e:
            sys.exit(e.exit_code)

    def make_context(self, info_name, args=None, **extra):
        args = get_os_args() if args is None else args
        ctx = Context(self, info_name=info_name, args=args, **extra)
        self.parse_args(ctx, ctx.args)
        return ctx

    def _create_parser(self, ctx):
        parser = argparse.ArgumentParser(prog=self.name, description=self.help)
        for param in self.params:
            if isinstance(param, Option):
                parser.add_argument(*param.param_decls, help=param.help, default=param.default, required=param.required)
            elif isinstance(param, Argument):
                parser.add_argument(*param.param_decls, help=param.help, default=param.default, nargs='?' if not param.required else None)
        return parser

class Group(Command):
    def __init__(self, name=None, **attrs):
        super().__init__(name, **attrs)
        self.commands = {}

    def command(self, *args, **kwargs):
        def decorator(f):
            cmd = command(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd
        return decorator

    def group(self, *args, **kwargs):
        def decorator(f):
            cmd = group(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd
        return decorator

    def add_command(self, cmd, name=None):
        name = name or cmd.name
        self.commands[name] = cmd

    def get_command(self, ctx, cmd_name):
        return self.commands.get(cmd_name)

    def invoke(self, ctx):
        if not ctx.args or ctx.args[0] not in self.commands:
            return super().invoke(ctx)
        cmd_name = ctx.args[0]
        cmd = self.commands[cmd_name]
        ctx.args = ctx.args[1:]
        return cmd.invoke(ctx)

class MultiCommand(Command):
    pass

class CommandCollection(MultiCommand):
    def __init__(self, name=None, sources=None, **attrs):
        super().__init__(name, **attrs)
        self.sources = sources or []

    def list_commands(self, ctx):
        rv = set()
        for source in self.sources:
            rv.update(source.list_commands(ctx))
        return sorted(rv)

    def get_command(self, ctx, name):
        for source in self.sources:
            cmd = source.get_command(ctx, name)
            if cmd is not None:
                return cmd
        return None