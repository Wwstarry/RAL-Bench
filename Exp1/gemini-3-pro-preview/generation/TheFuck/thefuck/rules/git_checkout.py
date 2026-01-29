# Rule: git checkout
# Detects: git checkout <typo>

import subprocess
from thefuck.utils import get_closest

def match(command):
    return ('git' in command.script_parts and 
            'checkout' in command.script_parts and
            "did not match any file(s) known to git" in command.stderr)

def get_new_command(command):
    parts = command.script_parts
    try:
        idx = parts.index('checkout')
        wanted = parts[idx+1]
    except IndexError:
        return []

    try:
        proc = subprocess.Popen('git branch -a', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, _ = proc.communicate()
        branches = [b.strip().replace('* ', '').split('/')[-1] for b in out.decode().splitlines()]
        
        best = get_closest(wanted, branches)
        if best:
            return command.script.replace(wanted, best)
    except OSError:
        pass
    return []