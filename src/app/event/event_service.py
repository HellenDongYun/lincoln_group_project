from src.app.admin.admin import Admin
from src.app.admin.admin_repository import AdminRepository
from src.app.event.event import Event
from src.app.event.event_repository import EventRepository


class EventService:

    def __init__(self):
        self.repository = EventRepository()

    def get_events(self, search_query: str = None, location_filter: str = None, date_filter: str = None) -> list[Event]:
        rows = self.repository.get_events(search_query, location_filter, date_filter)
        return [Event(**row) for row in rows]

    def get_unique_locations(self) -> list[str]:
        """Get all unique event locations for filter dropdown"""
        return self.repository.get_unique_locations()