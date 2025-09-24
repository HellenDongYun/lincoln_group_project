from dataclasses import dataclass
from datetime import datetime as dt


from src.app.common.datetime_format import DatetimeFormat



@dataclass
class Event:
    id: int = None
    group_id: int = None
    datetime: dt = None
    town: str = None
    name: str = None
    event_type: str = None
    description: str = None
    max_participants: int = None
    visibility: str = None
    created_by: int = None

    available_spaces: int = None
    # Additional fields for joined data
    group_name: str = None

    @property
    def datetime_str(self) -> str:
        return None if self.datetime is None else self.datetime.strftime(DatetimeFormat.NZ_SHORT_DATETIME.value)

    @property
    def is_public(self) -> bool:
        return self.visibility == 'public'



