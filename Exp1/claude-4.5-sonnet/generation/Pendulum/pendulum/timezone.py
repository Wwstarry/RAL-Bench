"""
Timezone handling.
"""

import datetime as dt
from datetime import timezone as dt_timezone
import re


# Common timezone offsets
_TIMEZONE_OFFSETS = {
    'UTC': 0,
    'GMT': 0,
    'EST': -5,
    'EDT': -4,
    'CST': -6,
    'CDT': -5,
    'MST': -7,
    'MDT': -6,
    'PST': -8,
    'PDT': -7,
    'CET': 1,
    'CEST': 2,
    'EET': 2,
    'EEST': 3,
    'JST': 9,
    'KST': 9,
    'IST': 5.5,
    'AEST': 10,
    'AEDT': 11,
}


# IANA timezone database (simplified)
_IANA_TIMEZONES = {
    'America/New_York': -5,
    'America/Chicago': -6,
    'America/Denver': -7,
    'America/Los_Angeles': -8,
    'America/Phoenix': -7,
    'America/Toronto': -5,
    'America/Vancouver': -8,
    'America/Mexico_City': -6,
    'America/Sao_Paulo': -3,
    'America/Argentina/Buenos_Aires': -3,
    'Europe/London': 0,
    'Europe/Paris': 1,
    'Europe/Berlin': 1,
    'Europe/Rome': 1,
    'Europe/Madrid': 1,
    'Europe/Amsterdam': 1,
    'Europe/Brussels': 1,
    'Europe/Vienna': 1,
    'Europe/Warsaw': 1,
    'Europe/Moscow': 3,
    'Europe/Istanbul': 3,
    'Europe/Athens': 2,
    'Asia/Tokyo': 9,
    'Asia/Seoul': 9,
    'Asia/Shanghai': 8,
    'Asia/Hong_Kong': 8,
    'Asia/Singapore': 8,
    'Asia/Bangkok': 7,
    'Asia/Dubai': 4,
    'Asia/Kolkata': 5.5,
    'Asia/Karachi': 5,
    'Asia/Jakarta': 7,
    'Australia/Sydney': 10,
    'Australia/Melbourne': 10,
    'Australia/Brisbane': 10,
    'Australia/Perth': 8,
    'Pacific/Auckland': 12,
    'Africa/Cairo': 2,
    'Africa/Johannesburg': 2,
    'Africa/Lagos': 1,
}


class Timezone(dt.tzinfo):
    """
    A timezone implementation.
    """

    def __init__(self, offset=0, name=None):
        """
        Initialize a Timezone.
        
        Args:
            offset: UTC offset in hours (can be float)
            name: Timezone name
        """
        self._offset = offset
        self._name = name or f"UTC{'+' if offset >= 0 else ''}{offset}"
        self.zone = self._name

    def utcoffset(self, dt):
        """
        Get the UTC offset.
        """
        hours = int(self._offset)
        minutes = int((abs(self._offset) - abs(hours)) * 60)
        return dt_timezone(dt.timedelta(hours=hours, minutes=minutes)).utcoffset(None)

    def tzname(self, dt):
        """
        Get the timezone name.
        """
        return self._name

    def dst(self, dt):
        """
        Get the DST offset (always 0 for our simple implementation).
        """
        return dt.timedelta(0)

    def __repr__(self):
        return f"Timezone('{self._name}')"

    def __str__(self):
        return self._name


def timezone(name):
    """
    Get a timezone by name.
    
    Args:
        name: Timezone name (e.g., 'UTC', 'America/New_York', 'EST', '+05:00')
    
    Returns:
        Timezone: A Timezone instance
    """
    if name is None or name == 'UTC':
        return Timezone(0, 'UTC')
    
    # Check if it's a common abbreviation
    if name.upper() in _TIMEZONE_OFFSETS:
        offset = _TIMEZONE_OFFSETS[name.upper()]
        return Timezone(offset, name.upper())
    
    # Check if it's an IANA timezone
    if name in _IANA_TIMEZONES:
        offset = _IANA_TIMEZONES[name]
        return Timezone(offset, name)
    
    # Check if it's an offset string like '+05:00' or '-08:00'
    offset_match = re.match(r'^([+-])(\d{1,2}):?(\d{2})?$', name)
    if offset_match:
        sign = 1 if offset_match.group(1) == '+' else -1
        hours = int(offset_match.group(2))
        minutes = int(offset_match.group(3) or 0)
        offset = sign * (hours + minutes / 60.0)
        return Timezone(offset, name)
    
    # Default to UTC if unknown
    return Timezone(0, name)


def local_timezone():
    """
    Get the local timezone.
    """
    # Get local offset
    now = dt.datetime.now()
    utc_now = dt.datetime.utcnow()
    offset = (now - utc_now).total_seconds() / 3600
    
    return Timezone(offset, 'local')