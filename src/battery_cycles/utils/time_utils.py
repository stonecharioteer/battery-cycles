"""Time and duration utilities."""

from datetime import datetime, timedelta


def format_duration(minutes: int | None) -> str:
    """Format duration in minutes to human-readable string.

    Args:
        minutes: Duration in minutes

    Returns:
        Formatted string like "2h 30m" or "45m"
    """
    if minutes is None:
        return "N/A"

    if minutes < 60:
        return f"{minutes}m"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes == 0:
        return f"{hours}h"

    return f"{hours}h {remaining_minutes}m"


def format_timedelta(td: timedelta | None) -> str:
    """Format timedelta to human-readable string.

    Args:
        td: Timedelta to format

    Returns:
        Formatted string like "2h 30m" or "3 days"
    """
    if td is None:
        return "N/A"

    total_seconds = int(td.total_seconds())

    if total_seconds < 60:
        return f"{total_seconds}s"

    if total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes}m"

    if total_seconds < 86400:  # Less than a day
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if minutes == 0:
            return f"{hours}h"
        return f"{hours}h {minutes}m"

    # Days
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    if hours == 0:
        return f"{days} day{'s' if days != 1 else ''}"
    return f"{days} day{'s' if days != 1 else ''}, {hours}h"


def format_time_ago(dt: datetime | None) -> str:
    """Format datetime as time ago from now.

    Args:
        dt: Datetime to format

    Returns:
        Formatted string like "2 hours ago" or "yesterday"
    """
    if dt is None:
        return "N/A"

    now = datetime.now()
    diff = now - dt

    return format_timedelta(diff) + " ago"


def format_datetime(dt: datetime | None, format_12h: bool = True) -> str:
    """Format datetime to readable string.

    Args:
        dt: Datetime to format
        format_12h: Use 12-hour format if True, 24-hour if False

    Returns:
        Formatted datetime string
    """
    if dt is None:
        return "N/A"

    if format_12h:
        return dt.strftime("%Y-%m-%d %I:%M %p")
    return dt.strftime("%Y-%m-%d %H:%M")
