import os
import sys

def echo(message=None, nl=True, err=False, color=None):
    file = sys.stderr if err else sys.stdout
    if message is not None:
        file.write(str(message))
    if nl:
        file.write('\n')
    file.flush()

def secho(message=None, nl=True, err=False, **styles):
    echo(message, nl=nl, err=err)

def prompt(text, default=None, hide_input=False, show_choices=True, err=False, **kwargs):
    echo(text, nl=False, err=err)
    if default is not None:
        echo(f" [{default}]", nl=False, err=err)
    echo(": ", nl=False, err=err)
    if hide_input:
        import getpass
        return getpass.getpass('')
    return input().strip() or default

def confirm(text, default=False, abort=False, err=False, **kwargs):
    while True:
        prompt_text = f"{text} [{'Y/n' if default else 'y/N'}]"
        value = prompt(prompt_text, default='' if default is None else None, err=err).lower()
        if not value:
            return default
        if value in ('y', 'yes'):
            return True
        if value in ('n', 'no'):
            if abort:
                raise Abort()
            return False
        echo("Error: invalid input", err=err)

def style(text, **kwargs):
    return text

def unstyle(text):
    return text

def clear():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def get_terminal_size():
    return (80, 24)

def edit(text=None, editor=None, env=None, **kwargs):
    return text

def launch(url, wait=False, locate=False):
    pass

def getchar(echo=False):
    import tty, termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    if echo:
        sys.stdout.write(ch)
    return ch

def pause(info='Press any key to continue ...', err=False):
    if info:
        echo(info, nl=False, err=err)
    try:
        getchar()
    except (KeyboardInterrupt, EOFError):
        pass
    if info:
        echo(err=err)