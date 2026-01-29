"""Serialization utilities"""

import pickle
import json

def pickle_loads(s):
    """Load pickle data"""
    return pickle.loads(s)

def pickle_dumps(obj):
    """Dump pickle data"""
    return pickle.dumps(obj)

def json_loads(s):
    """Load JSON data"""
    return json.loads(s)

def json_dumps(obj):
    """Dump JSON data"""
    return json.dumps(obj)