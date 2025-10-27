from src.app.event.event import Event
from src.app.event.event_repository import EventRepository


class EventService:

    def __init__(self):
        self.repository = EventRepository()

    def get_event_by_id(self, event_id: int) -> Event | None:
        row = self.repository.get_event_by_id(event_id)
        return Event(**row) if row else None