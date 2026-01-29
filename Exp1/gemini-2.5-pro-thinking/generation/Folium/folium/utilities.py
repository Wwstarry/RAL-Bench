# folium/utilities.py
import json
import re

def _validate_location(location):
    """Validate a location."""
    if isinstance(location, (list, tuple)) and len(location) == 2:
        try:
            return [float(location[0]), float(location[1])]
        except (ValueError, TypeError):
            pass
    raise ValueError(f"Invalid location: {location}")

def _parse_size(value):
    """Parse a size value."""
    if isinstance(value, (int, float)):
        return f"{value}px"
    return value

def _to_json(obj, **kwargs):
    """Serialize an object to a JSON string."""
    return json.dumps(obj, **kwargs)

def _camelize(key):
    """Convert snake_case to camelCase."""
    return re.sub(r"_(.)", lambda m: m.group(1).upper(), key)

def _parse_options(**kwargs):
    """Create a JSON string of options from keyword arguments."""
    options = {}
    for key, value in kwargs.items():
        if value is not None:
            options[_camelize(key)] = value
    return _to_json(options)