import os
import glob
import importlib

def load_rules():
    """Dynamically discover and return all rules in this package."""
    rules_dir = os.path.dirname(__file__)
    modules = []
    for path in glob.glob(os.path.join(rules_dir, "*.py")):
        base = os.path.basename(path)
        if base == "__init__.py":
            continue
        name, _ = os.path.splitext(base)
        modname = f"thefuck.rules.{name}"
        modules.append(importlib.import_module(modname))
    return modules

def get_rules():
    """Return a list of all rule modules."""
    return load_rules()