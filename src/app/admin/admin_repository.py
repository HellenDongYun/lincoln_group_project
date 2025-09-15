from flask import flash, request
from src.app.common.db.cursor import get_cursor
from src.app.common.db.repository import Repository


class AdminRepository(Repository):

    def get_admin_by_admin_id(self, admin_id: int):
        return self.fetchone(
            "SELECT * FROM Users WHERE id = %s;",
            (admin_id,)
        )
    @staticmethod
    def count_events(name=None, town=None):
        query = "SELECT COUNT(*) as total FROM Events WHERE 1=1"
        params = []

        if name:
            query += " AND name LIKE %s"
            params.append(f"%{name}%")
        if town:
            query += " AND town LIKE %s"
            params.append(f"%{town}%")

        with get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()["total"]

    @staticmethod
    def fetch_events(name=None, town=None, order="asc", limit=5, offset=0):
        query = """
            SELECT e.id, e.datetime, e.town, e.name, 
                   e.event_type, e.description, e.max_participants,
                   COUNT(DISTINCT CASE WHEN p.status = 'registered' THEN p.participant_id END) as participant_count,
                   COALESCE(SUM(v.spots), 0) as volunteer_slots_total,
                   COUNT(DISTINCT ev.volunteer_id) as assigned_volunteers
            FROM Events e
            LEFT JOIN Participants p ON e.id = p.event_id
            LEFT JOIN Vacancies v ON e.id = v.event_id
            LEFT JOIN Event_Volunteers ev ON e.id = ev.event_id
            WHERE e.datetime > CURRENT_DATE
        """
        params = []
        if name:
            query += " AND e.name LIKE %s"
            params.append(f"%{name}%")
        if town:
            query += " AND e.town LIKE %s"
            params.append(f"%{town}%")
            
        query += " GROUP BY e.id, e.datetime, e.town, e.name, e.event_type, e.description, e.max_participants"
        
        # order
        if order == "asc":
            query += " ORDER BY e.datetime ASC"
        elif order == "desc":
            query += " ORDER BY e.datetime DESC"

        # pagination
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
        
    @staticmethod     
    def get_event_by_id(cursor, event_id):
        cursor.execute("SELECT * FROM Events WHERE id = %s", (event_id,))
        return cursor.fetchone()
    
    @staticmethod
    def delete_event(cursor, event_id: int):
        # delete events
        cursor.execute("DELETE FROM Vacancies WHERE event_id = %s", (event_id,))
        cursor.execute("DELETE FROM Events WHERE id = %s", (event_id,))
    
    
    @staticmethod
    def get_volunteer_roles(cursor, event_id):
        cursor.execute("""
            SELECT vr.id, vr.name, vr.description, v.spots
            FROM Volunteer_Roles vr
            JOIN Vacancies v ON vr.id = v.role_id
            WHERE v.event_id = %s
        """, (event_id,))
        return cursor.fetchall()
    
    @staticmethod
    def get_event_participants(cursor, event_id):
        cursor.execute("""
            SELECT u.first_name, u.last_name, u.town, u.email, u.role, p.status,p.participant_id,p.event_id
            FROM Users u
            JOIN Participants p ON u.id = p.participant_id
            WHERE p.event_id = %s
        """, (event_id,))
        return cursor.fetchall()
    
    @staticmethod
    def count_event_participants(cursor, event_id):
        cursor.execute("SELECT COUNT(*) as count FROM Participants WHERE event_id = %s", (event_id,))
        return cursor.fetchone()['count']
    
    @staticmethod
    def sum_volunteer_spots(cursor, event_id):
        cursor.execute("SELECT COALESCE(SUM(spots), 0) as total_spots FROM Vacancies WHERE event_id = %s", (event_id,))
        return cursor.fetchone()['total_spots']
        
    @staticmethod
    def fetch_event_name(cursor, event_id):
        cursor.execute("SELECT name FROM Events WHERE id = %s", (event_id,))
        return cursor.fetchone()['name']

    @staticmethod
    def fetch_all_roles(cursor):
        cursor.execute("SELECT id, name FROM Volunteer_Roles")
        return cursor.fetchall()

    @staticmethod
    def fetch_assigned_roles(cursor, event_id):
        cursor.execute("""
            SELECT v.role_id, r.name, v.spots
            FROM Vacancies v
            JOIN Volunteer_Roles r ON v.role_id = r.id
            WHERE v.event_id = %s
        """, (event_id,))
        return cursor.fetchall()

    @staticmethod
    def delete_role_assignment(cursor, event_id, role_id):
        cursor.execute("DELETE FROM Vacancies WHERE role_id = %s AND event_id = %s", (role_id, event_id))

    @staticmethod
    def upsert_role_assignment(cursor, event_id, role_id, spots):
        cursor.execute("""
            INSERT INTO Vacancies (event_id, role_id, spots)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE spots = VALUES(spots)
        """, (event_id, role_id, spots))   
        
    def remove_volunteer_role(event_id):
        role_id = request.form.get("role_id")
        with get_cursor() as cursor:
            cursor.execute("DELETE FROM Vacancies WHERE role_id = %s AND event_id = %s", (role_id, event_id))
            flash("Volunteer role removed!", "success")     
            
    @staticmethod
    def update_user_role(cursor, user_id, role):
        query = "UPDATE Users SET role = %s WHERE id = %s"
        cursor.execute(query, (role, user_id))
        return cursor.rowcount > 0
    
    @staticmethod
    def update_user_status(cursor, user_id, status):
        query = "UPDATE Users SET status = %s WHERE id = %s"
        cursor.execute(query, (status, user_id))
        return cursor.rowcount > 0
    
    @staticmethod
    def get_user_by_id(cursor, user_id):
        cursor.execute("SELECT id, first_name, last_name, email, role, town, status, CONCAT(TRIM(first_name), ' ', TRIM(last_name)) AS full_name FROM Users WHERE id = %s", (user_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_all_users_simple(cursor, page=1, per_page=10, search_name=None, search_role=None):
        """Get users for role management - simpler version without event data"""
        query = """
            SELECT id, CONCAT(TRIM(first_name), ' ', TRIM(last_name)) AS full_name,
                   email, role, town, status
            FROM Users
            WHERE 1=1
        """
        
        params = []
        
        if search_name:
            query += " AND (LOWER(TRIM(first_name)) LIKE %s OR LOWER(TRIM(last_name)) LIKE %s)"
            name_term = f"%{search_name.lower()}%"
            params.extend([name_term, name_term])
            
        if search_role:
            query += " AND LOWER(role) = %s"
            params.append(search_role.lower())
            
        query += " ORDER BY last_name, first_name LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        try:
            cursor.execute(query, params)
            users = cursor.fetchall()
        except Exception as e:
            if "Unknown column 'status'" in str(e):
                # Retry without status column
                query = """
                    SELECT id, CONCAT(TRIM(first_name), ' ', TRIM(last_name)) AS full_name,
                           email, role, town, 'active' as status
                    FROM Users
                    WHERE 1=1
                """
                if search_name:
                    query += " AND (LOWER(TRIM(first_name)) LIKE %s OR LOWER(TRIM(last_name)) LIKE %s)"
                if search_role:
                    query += " AND LOWER(role) = %s"
                query += " ORDER BY last_name, first_name LIMIT %s OFFSET %s"
                cursor.execute(query, params)
                users = cursor.fetchall()
            else:
                raise e
        
        # Get total count
        count_query = "SELECT COUNT(*) as count FROM Users WHERE 1=1"
        count_params = []
        
        if search_name:
            count_query += " AND (LOWER(TRIM(first_name)) LIKE %s OR LOWER(TRIM(last_name)) LIKE %s)"
            name_term = f"%{search_name.lower()}%"
            count_params.extend([name_term, name_term])
            
        if search_role:
            count_query += " AND LOWER(role) = %s"
            count_params.append(search_role.lower())
            
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()['count']
        
        return users, total_count
   
    @staticmethod    
    def get_all_volunteer_roles(cursor,filters: dict = None, page: int = 1, per_page: int = 10):
        filters = filters or {}
        query = ("""
            SELECT vr.id AS volunteer_role_id, 
            vr.name AS volunteer_role_name, 
            vr.description AS volunteer_role_description, 
            v.spots AS volunteer_count, 
            e.datetime AS event_datetime, 
            e.town AS event_location, 
            e.name AS event_name, 
            e.id AS event_id,
            e.max_participants AS event_max_participants
            FROM Volunteer_Roles vr
            JOIN Vacancies v ON vr.id = v.role_id
            JOIN Events e ON v.event_id = e.id
            WHERE e.datetime > CURRENT_DATE
        """)
        params = []
        # filter
        if filters.get("role_name"):
            query += " AND vr.name LIKE %s"
            params.append(f"%{filters['role_name']}%")
        if filters.get("event_name"):
            query += " AND e.name LIKE %s"
            params.append(f"%{filters['event_name']}%")
        if filters.get("location"):
            query += " AND e.town LIKE %s"
            params.append(f"%{filters['location']}%")

        # order + pagination
        query += " ORDER BY e.datetime ASC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # get total count for pagination purpose
        count_query = "SELECT COUNT(*) as count FROM Volunteer_Roles vr JOIN Vacancies v ON vr.id = v.role_id JOIN Events e ON v.event_id = e.id WHERE e.datetime > CURRENT_DATE"
        count_params = []
        if filters.get("role_name"):
            count_query += " AND vr.name LIKE %s"
            count_params.append(f"%{filters['role_name']}%")
        if filters.get("event_name"):
            count_query += " AND e.name LIKE %s"
            count_params.append(f"%{filters['event_name']}%")
        if filters.get("location"):
            count_query += " AND e.town LIKE %s"
            count_params.append(f"%{filters['location']}%")

        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()["count" ]
        return rows, total_count   
    @staticmethod
    def update_participant_status(user_id: int, event_id: int, status: str):
        with get_cursor() as cursor:
            query = "UPDATE Participants SET status = %s WHERE participant_id = %s AND event_id = %s"
            cursor.execute(query, (status, user_id, event_id))
            return cursor.rowcount  
    
    @staticmethod    
    def get_results(cursor):
        cursor.execute("""
        SELECT r.total_seconds,CONCAT(u.first_name,' ', u.last_name) AS full_name,e.name AS event_name,e.town AS event_location,e.datetime AS event_time
        FROM Race_Results r
        JOIN Users u ON u.id = r.participant_id
        JOIN Events e ON r.event_id = e.id
        """)
        return cursor.fetchall()

    @staticmethod
    def fetch_upcoming_events_with_volunteers():
        """Fetch next 5 upcoming events with their volunteer requirements"""
        query = """
            SELECT 
                e.id as event_id,
                e.name as event_name,
                e.datetime as event_datetime,
                e.town as event_location,
                e.event_type,
                e.description,
                e.max_participants,
                COALESCE(p_count.registered_participants, 0) as registered_participants,
                vr.name as volunteer_role,
                v.spots as volunteer_spots_needed,
                COALESCE(ev_count.assigned_volunteers, 0) as assigned_volunteers
            FROM (
                SELECT * FROM Events 
                WHERE datetime > NOW() 
                ORDER BY datetime ASC 
                LIMIT 5
            ) e
            LEFT JOIN (
                SELECT event_id, COUNT(*) as registered_participants
                FROM Participants 
                WHERE status = 'registered'
                GROUP BY event_id
            ) p_count ON e.id = p_count.event_id
            LEFT JOIN Vacancies v ON e.id = v.event_id
            LEFT JOIN Volunteer_Roles vr ON v.role_id = vr.id
            LEFT JOIN (
                SELECT event_id, role_id, COUNT(*) as assigned_volunteers
                FROM Event_Volunteers
                GROUP BY event_id, role_id
            ) ev_count ON v.event_id = ev_count.event_id AND v.role_id = ev_count.role_id
            ORDER BY e.datetime ASC, vr.name
        """
        
        with get_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()
    
    @staticmethod    
    def get_event_participants(cursor, full_name=None, role=None, status=None, limit=10, offset=0):
        """Get event participants sorted by events starting soon"""
        query = '''
        SELECT CONCAT(TRIM(u.first_name), ' ', TRIM(u.last_name)) AS full_name,
        u.email, 
        u.role, 
        u.town, 
        u.id,
        p.status AS user_status,
        e.name,
        e.datetime AS event_datetime,
        e.id AS event_id
        FROM Users u
        LEFT JOIN Participants p ON u.id = p.participant_id
        LEFT JOIN Events e ON p.event_id = e.id
        WHERE 1=1
        '''
        params = []
        
        if full_name:
            query += " AND (LOWER(TRIM(u.first_name)) LIKE %s OR LOWER(TRIM(u.last_name)) LIKE %s)"
            name_term = f"%{full_name.lower()}%"
            params.extend([name_term, name_term])

        if role:
            query += " AND LOWER(u.role) LIKE %s"
            params.append(f"%{role.lower()}%")

        if status:
            query += " AND LOWER(p.status) LIKE %s"
            params.append(f"%{status.lower()}%")

        # Sort by event datetime (upcoming events first), then by user name
        query += """ ORDER BY 
            CASE WHEN e.datetime IS NULL THEN 1 ELSE 0 END,
            e.datetime ASC,
            u.first_name ASC, u.last_name ASC
            LIMIT %s OFFSET %s"""
        params.extend([limit, offset])
        cursor.execute(query, params)
        return cursor.fetchall()
    
    @staticmethod
    def count_event_participants(cursor, full_name=None, role=None, status=None):
        """Count event participants with filters"""
        query = '''
        SELECT COUNT(*) as count
        FROM Users u
        LEFT JOIN Participants p ON u.id = p.participant_id
        LEFT JOIN Events e ON p.event_id = e.id
        WHERE 1=1
        '''
        params = []
        
        if full_name:
            query += " AND (LOWER(TRIM(u.first_name)) LIKE %s OR LOWER(TRIM(u.last_name)) LIKE %s)"
            name_term = f"%{full_name.lower()}%"
            params.extend([name_term, name_term])

        if role:
            query += " AND LOWER(u.role) LIKE %s"
            params.append(f"%{role.lower()}%")

        if status:
            query += " AND LOWER(p.status) LIKE %s"
            params.append(f"%{status.lower()}%")

        cursor.execute(query, params)
        result = cursor.fetchone()
        return result['count'] if isinstance(result, dict) else result[0]