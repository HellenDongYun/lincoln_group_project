from enum import Enum

class DateFormat(Enum):
    NZ_DATETIME = "%d/%m/%Y %H:%M:%S"
    NZ_NUMERIC = "%d/%m/%Y"     # 20/01/2025
    NZ_SHORT = "%d %b %Y"       # 20 Jan 2025
    ISO = "%Y-%m-%d"            # 2025-01-20