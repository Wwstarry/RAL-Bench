import shlex

def parse_command_line(line):
    """Parse a command line into command and arguments."""
    parts = shlex.split(line)
    if not parts:
        return None, []
    cmd = parts[0]
    args = parts[1:]
    return cmd, args

def parse_options(args, option_defs=None):
    """
    Parse options from a list of arguments.
    option_defs: dict of option name to default value.
    Returns: dict of options, list of remaining args.
    """
    opts = {}
    rest = []
    option_defs = option_defs or {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('--'):
            name = arg[2:]
            if (i+1) < len(args) and not args[i+1].startswith('-'):
                opts[name] = args[i+1]
                i += 2
            else:
                opts[name] = True
                i += 1
        elif arg.startswith('-'):
            name = arg[1:]
            if (i+1) < len(args) and not args[i+1].startswith('-'):
                opts[name] = args[i+1]
                i += 2
            else:
                opts[name] = True
                i += 1
        else:
            rest.append(arg)
            i += 1
    # Fill in defaults
    for k, v in option_defs.items():
        if k not in opts:
            opts[k] = v
    return opts, rest

def statement_parser(line):
    """Parse a statement into command and args (for compatibility)."""
    cmd, args = parse_command_line(line)
    return {'command': cmd, 'args': args}