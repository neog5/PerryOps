from datetime import datetime, timedelta
from typing import Optional


def subtract_time(dt: datetime, days: int = 0, hours: int = 0, minutes: int = 0) -> datetime:
    """Return a new datetime obtained by subtracting the specified offset from dt.

    Args:
        dt: Anchor datetime (e.g., scheduled surgery date/time)
        days: Days to subtract
        hours: Hours to subtract
        minutes: Minutes to subtract

    Returns:
        datetime: dt minus the provided offset
    """
    if not isinstance(dt, datetime):
        raise TypeError("dt must be a datetime instance")
    return dt - timedelta(days=days, hours=hours, minutes=minutes)
