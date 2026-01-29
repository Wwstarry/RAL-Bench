import sys
import os
import subprocess
from . import corrector
from .types import Command
from .conf import settings
from . import __version__

def main():
    args = sys.argv[1:]
    
    if not args:
        return

    if args[0] in ('-v', '--version'):
        print('The Fuck {} using Python {}'.format(__version__, sys.version.split()[0]))
        return

    # In the reference implementation, arguments are the command parts.
    script = ' '.join(args)
    
    # Execute command to get output
    env = dict(os.environ)
    env.update(settings.env)
    
    try:
        # Run the command to capture stdout/stderr
        p = subprocess.Popen(script, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        stdout, stderr = p.communicate()
        stdout = stdout.decode('utf-8', 'replace')
        stderr = stderr.decode('utf-8', 'replace')
    except Exception as e:
        stdout = ''
        stderr = str(e)

    command = Command(script, stdout, stderr)
    
    corrected = corrector.get_corrected_commands(command)
    corrected = corrector.organize_commands(corrected)
    
    if corrected:
        # Print the best command to stdout
        # Since we must avoid interactive prompts for tests, we just output the best match.
        print(corrected[0].script)
    else:
        sys.exit(1)