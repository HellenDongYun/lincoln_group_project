"""
Timezone utility functions for converting UTC to New Zealand (Auckland) time
Uses Python's built-in datetime module (no external dependencies)
"""
from datetime import datetime, timezone, timedelta


# New Zealand timezone offset (NZST: UTC+12, NZDT: UTC+13 during daylight saving)
# This is a simplified approach - for production, consider using pytz for DST handling
def get_nz_offset():
    """
    Get NZ timezone offset based on current date
    NZDT (Daylight): Last Sunday of September to first Sunday of April (UTC+13)
    NZST (Standard): First Sunday of April to last Sunday of September (UTC+12)
    """
    # Simplified: Using UTC+13 for summer (Oct-Mar), UTC+12 for winter (Apr-Sep)
    now = datetime.now(timezone.utc)
    month = now.month

    # NZDT months (approximately): October to March (UTC+13)
    if month >= 10 or month <= 3:
        return timedelta(hours=13)
    # NZST months (approximately): April to September (UTC+12)
    else:
        return timedelta(hours=12)


def to_nz_time(utc_datetime):
    """
    Convert a UTC datetime to Auckland/NZ timezone

    Args:
        utc_datetime: A datetime object (assumed to be UTC)

    Returns:
        datetime: The datetime converted to NZ timezone
    """
    if utc_datetime is None:
        return None

    # If datetime is naive (no timezone info), assume it's UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)

    # Convert to NZ timezone
    nz_offset = get_nz_offset()
    nz_tz = timezone(nz_offset)
    nz_datetime = utc_datetime.astimezone(nz_tz)

    return nz_datetime


def format_nz_datetime(utc_datetime, format_string='%d %b %Y %H:%M'):
    """
    Convert UTC datetime to NZ time and format it

    Args:
        utc_datetime: A datetime object (assumed to be UTC)
        format_string: strftime format string (default: '20 Jan 2025 07:30')

    Returns:
        str: Formatted datetime string in NZ timezone
    """
    if utc_datetime is None:
        return ''

    nz_datetime = to_nz_time(utc_datetime)
    return nz_datetime.strftime(format_string)
