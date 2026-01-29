import json
import re


def get_name(element):
    """Returns the name of a Folium object."""
    return element._name


def _validate_location(location):
    """Validate a location."""
    if not isinstance(location, (list, tuple)) or len(location) != 2:
        raise ValueError("Location must be a list/tuple of length 2.")
    if not all(isinstance(x, (int, float)) for x in location):
        raise ValueError("Location values must be numeric.")
    return list(location)


def json_dump(obj, **kwargs):
    """A wrapper for json.dumps that handles common issues."""
    return json.dumps(obj, **kwargs)


def _camelify(s):
    """Converts snake_case to camelCase."""
    return re.sub(r"_(.)", lambda m: m.group(1).upper(), s)