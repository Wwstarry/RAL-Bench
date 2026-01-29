"""Tests for rules module."""

import pytest
from thefuck.rules import load_rules, Rule
from thefuck.command import Command


def test_load_rules():
    """Test loading rules."""
    rules = load_rules()
    assert isinstance(rules, list)
    assert all(isinstance(r, Rule) for r in rules)


def test_rule_creation():
    """Test creating a Rule object."""
    def match_fn(cmd):
        return True
    
    def get_corrected_fn(cmd):
        return ["corrected"]
    
    rule = Rule("test", match_fn, get_corrected_fn)
    assert rule.name == "test"
    assert rule.match(Command("test")) is True
    assert rule.get_corrected(Command("test")) == ["corrected"]