import difflib

def get_closest(word, possibilities, cutoff=0.6):
    matches = difflib.get_close_matches(word, possibilities, n=1, cutoff=cutoff)
    return matches[0] if matches else None

def replace_argument(script, search, replace):
    return script.replace(search, replace)