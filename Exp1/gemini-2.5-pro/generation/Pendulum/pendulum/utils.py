# -*- coding: utf-8 -*-

import datetime as _dt
from .timezone import Timezone

def _get_tzinfo(tz):
    """
    Returns a tzinfo instance from a string or a tzinfo instance.
    """
    if isinstance(tz, _dt.tzinfo):
        return tz
    
    if not isinstance(tz, str):
        raise TypeError("tz argument must be a string or a tzinfo instance")

    return Timezone(tz)