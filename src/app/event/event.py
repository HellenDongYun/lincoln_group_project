from dataclasses import dataclass
from datetime import datetime


from src.app.common.datetime_format import DatetimeFormat



@dataclass
class Event:
    id: int = None
    datetime: datetime = None
    town: str = None
    name: str = None
    event_type: str = None
    description: str = None
    max_participants: int = None

    available_spaces: int = None

    @property
    def datetime_str(self) -> str:
        return None if self.datetime is None else self.datetime.strftime(DatetimeFormat.NZ_SHORT_DATETIME.value)



