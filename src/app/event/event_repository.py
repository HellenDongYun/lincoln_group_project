from src.app.common.db.repository import Repository


class EventRepository(Repository):

    def get_event_by_id(self, event_id: int):
        """Fetch a single event record by its ID."""
        sql = "SELECT * FROM Events WHERE id = %s"
        return self.fetchone(sql, (event_id,))

