"""
Uses the IANA timezone database `Pacific/Auckland` so the correct offset
is applied automatically (NZST UTC+12, NZDT UTC+13). 
"""

from __future__ import annotations

from datetime import datetime, timezone

try:  
    from zoneinfo import ZoneInfo
except ImportError:  
    from backports.zoneinfo import ZoneInfo  # type: ignore


_NZ_TZ = ZoneInfo("Pacific/Auckland")


def get_nz_timezone() -> ZoneInfo:
    """Return the ZoneInfo instance for the Auckland timezone."""

    return _NZ_TZ


def to_nz_time(value: datetime | None) -> datetime | None:
    """Convert ``value`` to the Pacific/Auckland timezone.
    """

    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(_NZ_TZ)


def format_nz_datetime(value: datetime | None, format_string: str = "%d %b %Y %H:%M") -> str:


    nz_value = to_nz_time(value)
    if nz_value is None:
        return ""

    return nz_value.strftime(format_string)
