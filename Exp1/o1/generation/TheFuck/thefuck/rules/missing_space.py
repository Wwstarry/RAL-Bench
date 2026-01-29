import re

enabled_by_default = True

def match(command):
    # Simple check: if the script has something like 'ls-l' or 'cd..' etc.
    # We'll guess if there's a known command prefix + missing space + recognized argument.
    # Example: "ls-l" => "ls -l"
    if command.return_code != 0:
        # Heuristic: check common known pairs
        patterns = [
            r'^ls-l$',  # => "ls -l"
            r'^cd\.\.$' # => "cd .."
        ]
        for pat in patterns:
            if re.match(pat, command.script):
                return True
    return False

def get_new_command(command):
    if command.script == 'ls-l':
        return ['ls -l']
    if command.script == 'cd..':
        return ['cd ..']
    return []