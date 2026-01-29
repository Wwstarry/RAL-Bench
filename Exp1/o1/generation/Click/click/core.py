# click/core.py
# Core implementation of the command system, contexts, and parameter parsing.

import sys
import os

class Context:
    """
    A context holds information about the current execution,
    including command parameters, parent context, etc.
    """
    def __init__(self, command=None, parent=None, params=None):
        self.command = command
        self.parent = parent
        self.params = params or {}

    def forward(self, cmd, *args, **kwargs):
        """
        Forward invocation parameters to another command.
        """
        return cmd.invoke(Context(command=cmd, parent=self), *args, **kwargs)


class Parameter:
    """
    Base class for parameters (options or arguments).
    """
    def __init__(self, name, default=None, required=False, help=None,
                 prompt=False, is_flag=False, multiple=False):
        self.name = name
        self.default = default
        self.required = required
        self.help = help
        self.prompt = prompt
        self.is_flag = is_flag
        self.multiple = multiple

    def consume_value(self, args):
        """
        Pop the appropriate number of values from args.
        For flags, we return True/False if the flag is present/absent.
        For normal options/arguments, we consume one or more values.
        """
        if self.is_flag:
            # If the flag is found in args, return True, else False
            if self.name in args:
                # Remove the option name
                idx = args.index(self.name)
                del args[idx]
                return True
            return False
        # For normal parameters:
        if not args and self.required:
            raise RuntimeError(f"Missing required parameter '{self.name}'.")
        if not args:
            return self.default
        if self.multiple:
            # Return all remaining as a list
            vals = []
            while args:
                val = args.pop(0)
                if val.startswith("-"):
                    # push back
                    args.insert(0, val)
                    break
                vals.append(val)
            return vals if vals else self.default
        # single value
        return args.pop(0)

    def prompt_for_value(self):
        """
        If prompt is True, request value from stdin.
        """
        if not self.prompt:
            return self.default
        print(f"{self.name}: ", end="", file=sys.stderr)
        return sys.stdin.readline().strip() or self.default


class Argument(Parameter):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)


class Option(Parameter):
    def __init__(self, name, **kwargs):
        #  e.g. name could be '--count'
        super().__init__(name, **kwargs)


class Command:
    """
    Represents a command with a callback and a list of parameters.
    """
    def __init__(self, name=None, callback=None, params=None,
                 help=None, context_settings=None):
        self.name = name or (callback.__name__ if callback else None)
        self.callback = callback
        self.params = params or []
        self.help = help
        self.context_settings = context_settings or {}

    def parse_args(self, ctx, args):
        """
        Parse args based on self.params.
        For each parameter, consume a value from args or from prompt.
        """
        for p in self.params:
            if p.is_flag or (p.name.startswith("--") or p.name.startswith("-")):
                # For the sake of simplicity, let's store by param name without dashes.
                param_name = p.name.lstrip("-")
            else:
                param_name = p.name

            if p.is_flag:
                ctx.params[param_name] = p.consume_value(args)
            else:
                if p.prompt and not args:
                    ctx.params[param_name] = p.prompt_for_value()
                else:
                    ctx.params[param_name] = p.consume_value(args)

    def invoke(self, ctx, *args, **kwargs):
        """
        Invokes the callback associated with the command.
        """
        if not self.callback:
            raise RuntimeError("Command has no callback.")
        final_kwargs = {}
        final_kwargs.update(ctx.params)
        final_kwargs.update(kwargs)
        return self.callback(**final_kwargs)

    def get_help(self, ctx):
        """
        Generate help text for the command.
        """
        lines = []
        lines.append(f"Usage: {self.name or 'command'} [OPTIONS] [ARGS]...")
        if self.help:
            lines.append("")
            lines.append(self.help)
        lines.append("")
        lines.append("Options / Arguments:")
        for p in self.params:
            param_name = p.name
            required_str = " (required)" if p.required else ""
            default_str = f" (default: {p.default})" if p.default else ""
            lines.append(f"  {param_name}{required_str}{default_str}")
            if p.help:
                lines.append(f"    {p.help}")
        return "\n".join(lines)

    def format_help(self, ctx, formatter=None):
        # For simplicity, just print get_help output
        return self.get_help(ctx)

    def main(self, args=None, prog_name=None, **extra):
        """
        Entry point that parses command line arguments and invokes the command.
        """
        if args is None:
            args = sys.argv[1:]
        ctx = Context(self)
        try:
            self.parse_args(ctx, args)
            return self.invoke(ctx)
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(2)


class Group(Command):
    """
    A command that nests subcommands.
    """
    def __init__(self, name=None, params=None, help=None, context_settings=None):
        super().__init__(
            name=name,
            callback=None,
            params=params,
            help=help,
            context_settings=context_settings
        )
        self.commands = {}

    def add_command(self, cmd, name=None):
        cmd_name = name or cmd.name
        self.commands[cmd_name] = cmd

    def parse_args(self, ctx, args):
        """
        Identify if the first argument is a subcommand,
        then parse arguments for that subcommand.
        """
        if not args or args[0].startswith("-"):
            # parse group-level options
            for p in self.params:
                param_name = p.name.lstrip("-") if p.is_flag else p.name
                if p.is_flag:
                    ctx.params[param_name] = p.consume_value(args)
                else:
                    if p.prompt and not args:
                        ctx.params[param_name] = p.prompt_for_value()
                    else:
                        ctx.params[param_name] = p.consume_value(args)
            # no subcommand explicitly chosen
            return None

        subcmd_name = args.pop(0)
        subcmd = self.commands.get(subcmd_name)
        if not subcmd:
            raise RuntimeError(f"Unknown command '{subcmd_name}'")
        return subcmd

    def invoke(self, ctx, *args, **kwargs):
        # Groups do not have a direct callback, so invocation is handled
        # by subcommand if chosen, or print help if none.
        pass

    def main(self, args=None, prog_name=None, **extra):
        if args is None:
            args = sys.argv[1:]
        ctx = Context(self)
        try:
            subcmd = self.parse_args(ctx, args)
            if subcmd is None:
                # No subcommand found, show help
                print(self.format_help(ctx))
                return
            # Subcommand execution
            subctx = Context(subcmd, parent=ctx)
            subcmd.parse_args(subctx, args)
            return subcmd.invoke(subctx)
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(2)

    def format_help(self, ctx, formatter=None):
        lines = []
        lines.append(f"Usage: {self.name or 'group'} [OPTIONS] COMMAND [ARGS]...")
        if self.help:
            lines.append("")
            lines.append(self.help)
        lines.append("")
        lines.append("Options:")
        for p in self.params:
            param_name = p.name
            lines.append(f"  {param_name}")
        lines.append("")
        lines.append("Commands:")
        for cmd_name in sorted(self.commands):
            lines.append(f"  {cmd_name}")
        return "\n".join(lines)