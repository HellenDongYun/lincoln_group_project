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
            SELECT
                e.id,
                e.datetime,
                e.town,
                e.name,
                e.event_type,
                e.description,
                e.max_participants,
                COUNT(DISTINCT CASE WHEN ep.status = 'registered' THEN ep.user_id END) AS participant_count,
                (
                    SELECT COALESCE(SUM(etv.spots), 0)
                    FROM Event_Task_Vacancies etv
                    WHERE etv.event_id = e.id
                ) AS volunteer_slots_total,
                (
                    SELECT COUNT(DISTINCT eta.user_id)
                    FROM Event_Task_Assignments eta
                    WHERE eta.event_id = e.id
                ) AS assigned_volunteers
            FROM Events e
            LEFT JOIN Event_Participants ep ON e.id = ep.event_id
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
    def get_event_by_id(event_id):
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM Events WHERE id = %s", (event_id,))
            return cursor.fetchone()
    
    @staticmethod
    def delete_event(event_id: int):
        with get_cursor() as cursor:
            cursor.execute("DELETE FROM Event_Task_Vacancies WHERE event_id = %s", (event_id,))
            cursor.execute("DELETE FROM Events WHERE id = %s", (event_id,))
    
    
    @staticmethod
    def get_volunteer_roles(event_id):
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT vt.id AS id,
                       vt.name,
                       vt.description,
                       etv.spots
                FROM Event_Task_Vacancies etv
                JOIN Volunteer_Tasks vt ON etv.task_id = vt.id
                WHERE etv.event_id = %s
                ORDER BY vt.name
            """, (event_id,))
            return cursor.fetchall()
    
    @staticmethod
    def get_event_participants_by_event_id(event_id):
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT u.first_name, u.last_name, u.town, u.email, u.global_role, ep.status, ep.user_id, ep.event_id
                FROM Users u
                JOIN Event_Participants ep ON u.id = ep.user_id
                WHERE ep.event_id = %s
            """, (event_id,))
            return cursor.fetchall()
    
    @staticmethod
    def count_event_participants(event_id):
        with get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM Event_Participants WHERE event_id = %s", (event_id,))
            return cursor.fetchone()['count']
    
    @staticmethod
    def sum_volunteer_spots(event_id):
        with get_cursor() as cursor:
            cursor.execute("SELECT COALESCE(SUM(spots), 0) as total_spots FROM Event_Task_Vacancies WHERE event_id = %s", (event_id,))
            return cursor.fetchone()['total_spots']
        
    @staticmethod
    def fetch_event_name(event_id):
        with get_cursor() as cursor:
            cursor.execute("SELECT name FROM Events WHERE id = %s", (event_id,))
            return cursor.fetchone()['name']

    @staticmethod
    def fetch_all_roles():
        with get_cursor() as cursor:
            cursor.execute("SELECT id, name FROM Volunteer_Tasks")
            return cursor.fetchall()

    @staticmethod
    def fetch_assigned_roles(event_id):
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT etv.task_id AS role_id,
                       vt.name,
                       etv.spots
                FROM Event_Task_Vacancies etv
                JOIN Volunteer_Tasks vt ON etv.task_id = vt.id
                WHERE etv.event_id = %s
                ORDER BY vt.name
            """, (event_id,))
            return cursor.fetchall()

    @staticmethod
    def delete_role_assignment(event_id, role_id):
        with get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM Event_Task_Vacancies WHERE task_id = %s AND event_id = %s",
                (role_id, event_id)
            )

    @staticmethod
    def upsert_role_assignment(event_id, role_id, spots):
        with get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO Event_Task_Vacancies (event_id, task_id, spots)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE spots = VALUES(spots)
            """, (event_id, role_id, spots))   
        
    def remove_volunteer_role(event_id):
        role_id = request.form.get("role_id")
        with get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM Event_Task_Vacancies WHERE task_id = %s AND event_id = %s",
                (role_id, event_id)
            )
            flash("Volunteer role removed!", "success")     
            
    @staticmethod
    def update_user_role(user_id, role):
        with get_cursor() as cursor:
            query = "UPDATE Users SET global_role = %s WHERE id = %s"
            cursor.execute(query, (role, user_id))
            return cursor.rowcount > 0
    
    @staticmethod
    def update_user_status(user_id, status, reason: str = None, changed_by: int = None):
        with get_cursor() as cursor:
            # Update status
            query = "UPDATE Users SET status = %s WHERE id = %s"
            cursor.execute(query, (status, user_id))
            updated = cursor.rowcount > 0

            # Optional audit insert if table exists
            if updated:
                try:
                    cursor.execute(
                        """
                        INSERT INTO User_Status_Audit (user_id, new_status, reason, changed_by)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (user_id, status, reason, changed_by)
                    )
                except Exception as e:
                    # If the audit table doesn't exist, skip silently
                    if 'User_Status_Audit' not in str(e):
                        raise e
            return updated
    
    @staticmethod
    def get_user_by_id(user_id):
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT id, first_name, last_name, email, global_role AS role, town, status, "
                "CONCAT(TRIM(first_name), ' ', TRIM(last_name)) AS full_name FROM Users WHERE id = %s",
                (user_id,),
            )
            return cursor.fetchone()
    
    @staticmethod
    def get_all_users_simple(page=1, per_page=10, search_name=None, search_role=None):
        """Get users for role management - simpler version without event data"""
        with get_cursor() as cursor:
            query = """
                SELECT id, CONCAT(TRIM(first_name), ' ', TRIM(last_name)) AS full_name,
                       email, global_role AS role, town, status
                FROM Users
                WHERE 1=1
            """

            params = []

            if search_name:
                query += " AND (LOWER(TRIM(first_name)) LIKE %s OR LOWER(TRIM(last_name)) LIKE %s)"
                name_term = f"%{search_name.lower()}%"
                params.extend([name_term, name_term])

            if search_role:
                query += " AND LOWER(global_role) = %s"
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
                               email, global_role AS role, town, 'active' as status
                        FROM Users
                        WHERE 1=1
                    """
                    if search_name:
                        query += " AND (LOWER(TRIM(first_name)) LIKE %s OR LOWER(TRIM(last_name)) LIKE %s)"
                    if search_role:
                        query += " AND LOWER(global_role) = %s"
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
                count_query += " AND LOWER(global_role) = %s"
                count_params.append(search_role.lower())

            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()['count']

            return users, total_count
   
    @staticmethod    
    def get_all_volunteer_roles(filters: dict = None, page: int = 1, per_page: int = 10):
        filters = filters or {}
        with get_cursor() as cursor:
            query = ("""
                SELECT vt.id AS volunteer_role_id,
                       vt.name AS volunteer_role_name,
                       vt.description AS volunteer_role_description,
                       etv.spots AS volunteer_count,
                       e.datetime AS event_datetime,
                       e.town AS event_location,
                       e.name AS event_name,
                       e.id AS event_id,
                       e.max_participants AS event_max_participants
                FROM Volunteer_Tasks vt
                JOIN Event_Task_Vacancies etv ON vt.id = etv.task_id
                JOIN Events e ON etv.event_id = e.id
                WHERE e.datetime > CURRENT_DATE
            """)
            params = []

            if filters.get("role_name"):
                query += " AND vt.name LIKE %s"
                params.append(f"%{filters['role_name']}%")
            if filters.get("event_name"):
                query += " AND e.name LIKE %s"
                params.append(f"%{filters['event_name']}%")
            if filters.get("location"):
                query += " AND e.town LIKE %s"
                params.append(f"%{filters['location']}%")

            query += " ORDER BY e.datetime ASC LIMIT %s OFFSET %s"
            params.extend([per_page, (page - 1) * per_page])
            cursor.execute(query, params)
            rows = cursor.fetchall()

            count_query = (
                "SELECT COUNT(*) as count "
                "FROM Volunteer_Tasks vt "
                "JOIN Event_Task_Vacancies etv ON vt.id = etv.task_id "
                "JOIN Events e ON etv.event_id = e.id "
                "WHERE e.datetime > CURRENT_DATE"
            )
            count_params = []
            if filters.get("role_name"):
                count_query += " AND vt.name LIKE %s"
                count_params.append(f"%{filters['role_name']}%")
            if filters.get("event_name"):
                count_query += " AND e.name LIKE %s"
                count_params.append(f"%{filters['event_name']}%")
            if filters.get("location"):
                count_query += " AND e.town LIKE %s"
                count_params.append(f"%{filters['location']}%")

            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()["count"]

            return rows, total_count   

    @staticmethod
    def fetch_group_overview(filters=None, limit=6):
        filters = filters or {}
        with get_cursor() as cursor:
            query = """
                SELECT
                    g.id AS group_id,
                    g.name,
                    g.description,
                    g.town,
                    g.visibility,
                    g.status,
                    g.created_by,
                    COALESCE(COUNT(DISTINCT CASE WHEN gm.member_status = 'active' THEN gm.user_id END), 0) AS member_count,
                    COALESCE(COUNT(DISTINCT CASE WHEN gm.member_status = 'active' AND gm.group_role = 'manager' THEN gm.user_id END), 0) AS manager_count,
                    GROUP_CONCAT(DISTINCT CASE WHEN gm.member_status = 'active' AND gm.group_role = 'manager' THEN CONCAT(TRIM(u.first_name), ' ', TRIM(u.last_name)) END ORDER BY u.first_name, u.last_name SEPARATOR '|') AS manager_names,
                    COALESCE(COUNT(DISTINCT CASE WHEN e.datetime >= NOW() THEN e.id END), 0) AS upcoming_events_count
                FROM Community_Groups g
                LEFT JOIN Group_Memberships gm ON gm.group_id = g.id
                LEFT JOIN Users u ON gm.user_id = u.id
                LEFT JOIN Events e ON e.group_id = g.id AND e.datetime >= NOW()
                WHERE 1=1
            """

            params = []

            search_term = filters.get('search')
            if search_term:
                like_pattern = f"%{search_term}%"
                query += " AND (g.name LIKE %s OR g.description LIKE %s)"
                params.extend([like_pattern, like_pattern])

            visibility = filters.get('visibility')
            if visibility:
                query += " AND g.visibility = %s"
                params.append(visibility)

            status = filters.get('status')
            if status:
                query += " AND g.status = %s"
                params.append(status)

            town = filters.get('town')
            if town:
                query += " AND g.town = %s"
                params.append(town)

            query += """
                GROUP BY g.id, g.name, g.description, g.town, g.visibility, g.status, g.created_by
            """

            if filters.get('has_events') == 'yes':
                query += " HAVING upcoming_events_count > 0"

            query += " ORDER BY upcoming_events_count DESC, member_count DESC, g.name ASC"

            if limit:
                query += " LIMIT %s"
                params.append(limit)

            cursor.execute(query, params)
            return cursor.fetchall()

    @staticmethod
    def fetch_pending_group_applications():
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT ga.id, ga.applicant_id, ga.proposed_name, ga.proposed_description,
                       ga.proposed_town, ga.visibility, ga.status,
                       u.first_name, u.last_name, u.email
                FROM Group_Applications ga
                JOIN Users u ON ga.applicant_id = u.id
                WHERE ga.status = 'pending'
                ORDER BY ga.id ASC
            """)
            return cursor.fetchall()

    @staticmethod
    def fetch_group_filter_options():
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT town
                FROM Community_Groups
                WHERE town IS NOT NULL AND town <> ''
                ORDER BY town ASC
            """)
            towns = [row['town'] for row in cursor.fetchall()]
            return {
                'towns': towns
            }

    @staticmethod
    def fetch_event_filter_options():
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT event_type
                FROM Events
                WHERE event_type IS NOT NULL AND event_type <> ''
                ORDER BY event_type ASC
            """)
            event_types = [row['event_type'] for row in cursor.fetchall()]

            cursor.execute("""
                SELECT DISTINCT town
                FROM Events
                WHERE town IS NOT NULL AND town <> ''
                ORDER BY town ASC
            """)
            event_towns = [row['town'] for row in cursor.fetchall()]

            return {
                'event_types': event_types,
                'event_towns': event_towns
            }

    @staticmethod
    def fetch_monitoring_metrics(timeframe_days=30):
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM Community_Groups) AS total_groups,
                    (SELECT COUNT(*) FROM Community_Groups WHERE status = 'active') AS active_groups,
                    (SELECT COUNT(*) FROM Group_Applications WHERE status = 'pending') AS pending_applications,
                    (SELECT COUNT(DISTINCT CASE WHEN gm.group_role = 'manager' AND gm.member_status = 'active' THEN gm.user_id END) FROM Group_Memberships gm) AS active_managers,
                    (SELECT COUNT(DISTINCT CASE WHEN gm.member_status = 'active' THEN gm.user_id END) FROM Group_Memberships gm) AS active_members,
                    (SELECT COUNT(*) FROM Events WHERE datetime >= NOW() AND datetime <= DATE_ADD(NOW(), INTERVAL %s DAY)) AS upcoming_events_window,
                    (SELECT COUNT(DISTINCT CASE WHEN ep.status = 'registered' THEN ep.event_id END) FROM Event_Participants ep) AS events_with_participants
            """, (timeframe_days,))
            return cursor.fetchone()

    @staticmethod
    def find_user_by_email(email):
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT id, first_name, last_name, email, global_role
                FROM Users
                WHERE LOWER(email) = LOWER(%s)
            """, (email,))
            return cursor.fetchone()
    @staticmethod
    def update_participant_status(user_id: int, event_id: int, status: str):
        with get_cursor() as cursor:
            query = "UPDATE Event_Participants SET status = %s WHERE user_id = %s AND event_id = %s"
            cursor.execute(query, (status, user_id, event_id))
            return cursor.rowcount  
    
    @staticmethod    
    def get_results():
        with get_cursor() as cursor:
            cursor.execute("""
            SELECT r.total_seconds,CONCAT(u.first_name,' ', u.last_name) AS full_name,e.name AS event_name,e.town AS event_location,e.datetime AS event_time
        FROM Event_Results r
            JOIN Users u ON u.id = r.participant_id
            JOIN Events e ON r.event_id = e.id
            """)
            return cursor.fetchall()

    @staticmethod
    def fetch_upcoming_events_with_volunteers(event_filters=None, limit=5):
        """Fetch upcoming events with volunteer requirements using optional filters"""
        event_filters = event_filters or {}
        subquery = "SELECT * FROM Events WHERE datetime > NOW()"
        params = []

        timeframe = event_filters.get("timeframe")
        if timeframe and timeframe != "all":
            try:
                days = max(1, int(timeframe))
                subquery += " AND datetime <= DATE_ADD(NOW(), INTERVAL %s DAY)"
                params.append(days)
            except ValueError:
                pass

        event_type = event_filters.get("type")
        if event_type:
            subquery += " AND event_type = %s"
            params.append(event_type)

        event_town = event_filters.get("town")
        if event_town:
            subquery += " AND town = %s"
            params.append(event_town)

        search_term = event_filters.get("search")
        if search_term:
            like_pattern = f"%{search_term}%"
            subquery += " AND (name LIKE %s OR description LIKE %s)"
            params.extend([like_pattern, like_pattern])

        subquery += " ORDER BY datetime ASC LIMIT %s"
        params.append(limit)

        query = f"""
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
            FROM ({subquery}) e
            LEFT JOIN (
                SELECT event_id, COUNT(*) as registered_participants
                FROM Event_Participants 
                WHERE status = 'registered'
                GROUP BY event_id
            ) p_count ON e.id = p_count.event_id
            LEFT JOIN Event_Task_Vacancies v ON e.id = v.event_id
            LEFT JOIN Volunteer_Tasks vr ON v.task_id = vr.id
            LEFT JOIN (
                SELECT event_id, task_id, COUNT(*) as assigned_volunteers
                FROM Event_Task_Assignments
                GROUP BY event_id, task_id
            ) ev_count ON v.event_id = ev_count.event_id AND v.task_id = ev_count.task_id
            ORDER BY e.datetime ASC, vr.name
        """

        with get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    @staticmethod    
    def get_event_participants_filtered(full_name=None, role=None, status=None, limit=10, offset=0):
        """Get event participants sorted by events starting soon"""
        with get_cursor() as cursor:
            query = '''
            SELECT CONCAT(TRIM(u.first_name), ' ', TRIM(u.last_name)) AS full_name,
            u.email, 
            u.global_role as role, 
            u.town, 
            u.id,
            ep.status AS user_status,
            e.name,
            e.datetime AS event_datetime,
            e.id AS event_id
            FROM Users u
            LEFT JOIN Event_Participants ep ON u.id = ep.user_id
            LEFT JOIN Events e ON ep.event_id = e.id
            WHERE 1=1
            '''
            params = []

            if full_name:
                query += " AND (LOWER(TRIM(u.first_name)) LIKE %s OR LOWER(TRIM(u.last_name)) LIKE %s)"
                name_term = f"%{full_name.lower()}%"
                params.extend([name_term, name_term])

            if role:
                query += " AND LOWER(u.global_role) LIKE %s"
                params.append(f"%{role.lower()}%")

            if status:
                query += " AND LOWER(ep.status) LIKE %s"
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
    def count_event_participants_filtered(full_name=None, role=None, status=None):
        """Count event participants with filters"""
        with get_cursor() as cursor:
            query = '''
            SELECT COUNT(*) as count
            FROM Users u
            LEFT JOIN Event_Participants ep ON u.id = ep.user_id
            LEFT JOIN Events e ON ep.event_id = e.id
            WHERE 1=1
            '''
            params = []

            if full_name:
                query += " AND (LOWER(TRIM(u.first_name)) LIKE %s OR LOWER(TRIM(u.last_name)) LIKE %s)"
                name_term = f"%{full_name.lower()}%"
                params.extend([name_term, name_term])

            if role:
                query += " AND LOWER(u.global_role) LIKE %s"
                params.append(f"%{role.lower()}%")

            if status:
                query += " AND LOWER(ep.status) LIKE %s"
                params.append(f"%{status.lower()}%")

            cursor.execute(query, params)
            result = cursor.fetchone()
            return result['count'] if isinstance(result, dict) else result[0]