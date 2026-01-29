import shlex

def parse_args(argstr):
    """
    Parse a string of arguments into a list, respecting quotes.
    """
    try:
        return shlex.split(argstr)
    except ValueError as e:
        # Could not parse arguments
        raise ValueError(f'Error parsing arguments: {e}')

def parse_options(argstr, option_prefix='-'):
    """
    Parse options from a string into a dict.
    Supports options like -a, --option, -b value, --option=value
    Returns (options_dict, remaining_args_list)
    """
    args = parse_args(argstr)
    options = {}
    remaining = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('--'):
            if '=' in arg:
                key, val = arg[2:].split('=', 1)
                options[key] = val
            else:
                key = arg[2:]
                # Check if next arg is value or another option
                if i + 1 < len(args) and not args[i + 1].startswith(option_prefix):
                    options[key] = args[i + 1]
                    i += 1
                else:
                    options[key] = True
        elif arg.startswith('-') and len(arg) > 1:
            # Short options cluster or single
            shorts = arg[1:]
            if len(shorts) > 1:
                # Clustered short options, all True
                for ch in shorts:
                    options[ch] = True
            else:
                key = shorts
                # Check if next arg is value or another option
                if i + 1 < len(args) and not args[i + 1].startswith(option_prefix):
                    options[key] = args[i + 1]
                    i += 1
                else:
                    options[key] = True
        else:
            remaining.append(arg)
        i += 1
    return options, remaining