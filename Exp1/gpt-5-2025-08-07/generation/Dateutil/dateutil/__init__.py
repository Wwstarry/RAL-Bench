"""
Lightweight pure-Python subset of python-dateutil core API.

Provided modules:
- dateutil.parser.parse: Flexible datetime string parser
- dateutil.relativedelta.relativedelta: Calendar-aware arithmetic
- dateutil.rrule.rrule: Recurrence rules (daily/weekly), constants, weekday specifiers
- dateutil.tz: Time zone utilities, including tz.UTC and tz.gettz
"""

from . import parser
from . import relativedelta
from . import rrule
from . import tz

__all__ = ["parser", "relativedelta", "rrule", "tz"]

# Provide a version attribute for compatibility
__version__ = "0.1.0"