from src.app.common.db.repository import Repository


class EventRepository(Repository):

    def get_events(self, search_query: str = None, location_filter: str = None, date_filter: str = None):
        sql = """
                   SELECT
                       e.*,
                       (e.max_participants - COALESCE(COUNT(ep.user_id), 0)) AS available_spaces
                   FROM Events e
                            LEFT JOIN Event_Participants ep
                                      ON ep.event_id = e.id AND ep.status = 'registered'
                   WHERE e.datetime > NOW()
                   """

        where_conditions = []
        params = []

        # Search functionality - only for event name and location
        if search_query and search_query.strip():
            search_param = f"%{search_query.strip()}%"
            where_conditions.append("(e.name LIKE %s OR e.town LIKE %s)")
            params.extend([search_param, search_param])

        # Location filter
        if location_filter and location_filter.strip():
            where_conditions.append("e.town = %s")
            params.append(location_filter.strip())

        # Date filter - handle new time period options
        if date_filter and date_filter.strip():
            if date_filter.strip() == "next_2_weeks":
                where_conditions.append("e.datetime <= DATE_ADD(NOW(), INTERVAL 2 WEEK)")
            elif date_filter.strip() == "next_month":
                where_conditions.append("e.datetime <= DATE_ADD(NOW(), INTERVAL 1 MONTH)")
            else:
                # Fallback for specific date (if still needed)
                where_conditions.append("DATE(e.datetime) = %s")
                params.append(date_filter.strip())

        # Add additional WHERE conditions if any
        if where_conditions:
            additional_where = " AND " + " AND ".join(where_conditions)
            sql += additional_where

        group_order = " GROUP BY e.id ORDER BY e.datetime;"
        
        return self.fetchall(sql + group_order, tuple(params) if params else None)

    def get_unique_locations(self):
        """Get all unique event locations for the filter dropdown (only for future events)"""
        sql = """
            SELECT DISTINCT town 
            FROM Events 
            WHERE town IS NOT NULL AND town != '' AND datetime > NOW()
            ORDER BY town
        """
        try:
            rows = self.fetchall(sql)
            return [row['town'] for row in rows]
        except Exception as e:
            print(f"Database error in get_unique_locations: {e}")
            return []

    def get_event_by_id(self, event_id: int):
        """Fetch a single event record by its ID."""
        sql = "SELECT * FROM Events WHERE id = %s"
        return self.fetchone(sql, (event_id,))

