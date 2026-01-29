"""
Configuration handling for TheFuck.
"""

import os
import json
from typing import Any, Dict, Optional


# Default settings
settings = {
    'no_confirm': False,
    'force_match': False,
    'auto_select': False,
    'rules': [],
    'exclude_rules': [],
    'priority': {},
    'wait_command': 3,
    'require_confirmation': True,
    'history_limit': 9999,
    'debug': False,
}


def load_settings() -> None:
    """Load settings from the configuration file."""
    config_path = os.path.expanduser('~/.thefuck/settings.json')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_settings = json.load(f)
                settings.update(user_settings)
        except (json.JSONDecodeError, OSError):
            # If there's an error reading the config, use defaults
            pass


def save_settings() -> None:
    """Save current settings to the configuration file."""
    config_path = os.path.expanduser('~/.thefuck/settings.json')
    
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(settings, f, indent=2)
    except OSError:
        # If there's an error saving, just continue
        pass


# Load settings when the module is imported
load_settings()