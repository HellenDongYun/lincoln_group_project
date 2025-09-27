from src.app.common.db.repository import Repository

class HomeService(Repository): 
    def get_upcoming_events(self, limit=5):
        """Get upcoming events for home page display"""
        sql = """
            SELECT 
                id as Event_ID,
                name as Event_Name,
                datetime as Event_DateTime,
                town as Event_Location,
                event_type as Event_Type,
                description as Description,
                max_participants as Max_Participants,
                COALESCE(participant_count.registered, 0) as Registered_Count
            FROM Events e
            LEFT JOIN (
                SELECT event_id, COUNT(*) as registered
                FROM Event_Participants 
                WHERE status = 'registered'
                GROUP BY event_id
            ) participant_count ON e.id = participant_count.event_id
            WHERE datetime > NOW()
            ORDER BY datetime ASC
            LIMIT %s
        """
        try:
            return self.fetchall(sql, (limit,))
        except Exception as e:
            print(f"Database error in get_upcoming_events: {e}")
            return []
    def home_filter_events(limit,location="", event_type="", date_str=""):
        return Repository.home_filter_events(limit,location, event_type, date_str)
    def home_filter_groups():
        return Repository.home_filter_groups() 