import pkgutil
import importlib

def get_rules():
    rules = []
    for _, name, _ in pkgutil.iter_modules(__path__):
        if name != '__init__':
            try:
                module = importlib.import_module('.' + name, __package__)
                rules.append(module)
            except ImportError:
                pass
    return rules