from enum import Enum

class DatetimeFormat(Enum):
    NZ_SHORT_DATETIME = "%d %b %Y %H:%M"    # 20 Jan 2025 07:30
    NZ_SHORT = "%d %b %Y"                   # 20 Jan 2025
    NZ_NUMERIC = "%d/%m/%Y"                 # 20/01/2025
    ISO = "%Y-%m-%d"                        # 2025-01-20