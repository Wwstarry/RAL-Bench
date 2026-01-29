import difflib
import os

def get_close_matches(word, possibilities, n=3, cutoff=0.6):
    """Wrapper around difflib.get_close_matches."""
    return difflib.get_close_matches(word, possibilities, n, cutoff)

def get_all_executables():
    """Returns a sorted list of all executable files in PATH."""
    executables = set()
    for path in os.environ.get('PATH', '').split(os.pathsep):
        try:
            for file in os.listdir(path):
                full_path = os.path.join(path, file)
                if os.access(full_path, os.X_OK) and not os.path.isdir(full_path):
                    executables.add(file)
        except OSError:
            # Path doesn't exist or isn't a directory
            pass
    return sorted(list(executables))