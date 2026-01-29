import os
import sys
import contextlib

def echo_via_pager(text, color=None):
    pager = os.environ.get('PAGER', 'more')
    if pager == 'more':
        os.system(f'more <<EOF\n{text}\nEOF')
    else:
        os.system(f'echo "{text}" | {pager}')

@contextlib.contextmanager
def progressbar(length, label=None, **kwargs):
    yield

def format_filename(filename, shorten=False):
    return filename

def get_app_dir(app_name, roaming=True, force_posix=False):
    if sys.platform.startswith('win'):
        key = 'APPDATA' if roaming else 'LOCALAPPDATA'
        folder = os.environ.get(key)
        if folder is None:
            folder = os.path.expanduser('~')
        return os.path.join(folder, app_name)
    if force_posix or sys.platform == 'darwin':
        return os.path.join(os.path.expanduser('~'), f'.{app_name}')
    return os.path.join(os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config')), app_name)

def open_file(filename, mode='r', encoding=None, errors='strict'):
    return open(filename, mode, encoding=encoding, errors=errors)

def get_os_args():
    return sys.argv[1:]