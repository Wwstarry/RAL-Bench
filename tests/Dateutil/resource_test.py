from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("DATEUTIL_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "dateutil" / "src"
else:
    REPO_ROOT = ROOT / "generation" / "Dateutil"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dateutil import tz  # type: ignore  # noqa: E402
from dateutil.relativedelta import relativedelta  # type: ignore  # noqa: E402
from dateutil.rrule import rrule, WEEKLY, TU, TH  # type: ignore  # noqa: E402


def _generate_meeting_schedule(
    start_date: dt.date,
    end_date: dt.date,
    offset_hours: int,
) -> List[dt.datetime]:
    """Generate a recurring meeting schedule between two dates.

    We schedule a meeting every Tuesday and Thursday at 10:00 in a fixed-offset
    local time zone defined by offset_hours.
    """
    local_tz = tz.tzoffset("LOCAL", offset_hours * 3600)

    start_local = dt.datetime(
        start_date.year,
        start_date.month,
        start_date.day,
        10,
        0,
        0,
        tzinfo=local_tz,
    )

    # rrule works on datetimes in local time; we stop when date > end_date.
    rule = rrule(
        WEEKLY,
        dtstart=start_local,
        until=dt.datetime(
            end_date.year,
            end_date.month,
            end_date.day,
            23,
            59,
            59,
            tzinfo=local_tz,
        ),
        byweekday=(TU, TH),
    )

    return list(rule)


def test_meeting_schedule_integration() -> None:
    """Integration test for building a recurring meeting schedule."""
    start = dt.date(2020, 1, 1)
    end = dt.date(2020, 2, 29)

    # Approximate "Europe/Berlin" as UTC+1 for this test.
    meetings = _generate_meeting_schedule(start, end, offset_hours=1)

    # There should be a reasonable number of meetings in this range.
    assert 10 <= len(meetings) <= 25

    # All meetings should be at 10:00 local time.
    for m in meetings:
        assert m.hour == 10
        assert m.minute == 0
        assert m.tzinfo is not None

    # Meetings should be strictly increasing.
    for prev, curr in zip(meetings, meetings[1:]):
        assert curr > prev

    # The span between first and last meeting should be close to the overall range.
    total_span = meetings[-1] - meetings[0]
    date_span = dt.datetime.combine(end, dt.time(23, 59, 59)) - dt.datetime.combine(
        start, dt.time(0, 0, 0)
    )
    assert total_span.total_seconds() > 0
    # Not a strict requirement, but should be within a factor.
    assert total_span.total_seconds() <= date_span.total_seconds()


def test_duration_between_two_events_with_relativedelta() -> None:
    """Use relativedelta to compute calendar duration between first and last meeting."""
    start = dt.date(2020, 1, 1)
    end = dt.date(2020, 3, 31)

    # Approximate "America/New_York" as UTC-5 for this test.
    meetings = _generate_meeting_schedule(start, end, offset_hours=-5)
    assert len(meetings) > 0

    first = meetings[0]
    last = meetings[-1]

    delta = relativedelta(last, first)

    # The total duration should be several weeks.
    weeks = delta.years * 52 + delta.months * 4 + delta.days // 7
    assert weeks >= 4
