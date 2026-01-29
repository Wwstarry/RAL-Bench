# This module can provide formatting utilities if needed.
# For now, we keep it minimal as the core formatting is done in DateTime.to_iso8601_string and diff_for_humans.

def format_iso8601(dt):
    # dt is a pendulum.datetime.DateTime instance
    return dt.to_iso8601_string()

def format_diff_for_humans(dt, other=None, absolute=False):
    return dt.diff_for_humans(other, absolute)