from src.app.common.db.cursor import get_cursor
from typing import Optional, List, Dict

class SupportRepository:
    #Repository for handling support request database operations

    @staticmethod
    def create_support_request(user_id: int, issue_type: str, subject: str,
                               description: str, screenshot_path: Optional[str] = None,
                               priority: str = 'medium') -> int:
        #Create a new support request and return its ID
        with get_cursor() as cursor:
            cursor.execute("""INSERT INTO Support_Requests
                (user_id, issue_type, subject, description, screenshot_path, priority, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'new')""", 
                (user_id, issue_type, subject, description, screenshot_path, priority))
            return cursor.lastrowid

    @staticmethod
    def get_user_support_requests(user_id: int) -> List[Dict]:
        #Get all support requests for a specific user
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    sr.id,
                    sr.issue_type,
                    sr.subject,
                    sr.description,
                    sr.status,
                    sr.priority,
                    sr.created_at,
                    sr.updated_at,
                    sr.assigned_to,
                    u.first_name AS assigned_first_name,
                    u.last_name AS assigned_last_name
                FROM Support_Requests sr
                LEFT JOIN Users u ON sr.assigned_to = u.id
                WHERE sr.user_id = %s
                ORDER BY sr.created_at DESC
            """, (user_id,))
            return cursor.fetchall()

    @staticmethod
    def get_support_request_by_id(request_id: int) -> Optional[Dict]:
        #Get a specific support request by ID
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    sr.id,
                    sr.user_id,
                    sr.issue_type,
                    sr.subject,
                    sr.description,
                    sr.screenshot_path,
                    sr.status,
                    sr.priority,
                    sr.assigned_to,
                    sr.created_at,
                    sr.updated_at,
                    u.first_name,
                    u.last_name,
                    u.email,
                    assigned.first_name AS assigned_first_name,
                    assigned.last_name AS assigned_last_name
                FROM Support_Requests sr
                INNER JOIN Users u ON sr.user_id = u.id
                LEFT JOIN Users assigned ON sr.assigned_to = assigned.id
                WHERE sr.id = %s
            """, (request_id,))
            return cursor.fetchone()

    @staticmethod
    def get_request_comments(request_id: int) -> List[Dict]:
        #Get all comments for a support request
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    c.id,
                    c.comment,
                    c.is_staff_reply,
                    c.created_at,
                    u.first_name,
                    u.last_name,
                    u.global_role
                FROM Support_Request_Comments c
                INNER JOIN Users u ON c.user_id = u.id
                WHERE c.request_id = %s
                ORDER BY c.created_at DESC
            """, (request_id,))
            return cursor.fetchall()

    @staticmethod
    def add_comment(request_id: int, user_id: int, comment: str,
                    is_staff_reply: bool = False) -> int:
        #Add a comment to a support request
        with get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO Support_Request_Comments
                (request_id, user_id, comment, is_staff_reply)
                VALUES (%s, %s, %s, %s)
            """, (request_id, user_id, comment, is_staff_reply))
            return cursor.lastrowid

    @staticmethod
    def update_request_status(request_id: int, new_status: str) -> bool:
        #Update the status of a support request
        with get_cursor() as cursor:
            cursor.execute("""
                UPDATE Support_Requests
                SET status = %s, updated_at = NOW()
                WHERE id = %s
            """, (new_status, request_id))
            return cursor.rowcount > 0

    @staticmethod
    def assign_request(request_id: int, assigned_to: Optional[int]) -> bool:
        #Assign a support request to a staff member
        with get_cursor() as cursor:
            cursor.execute("""
                UPDATE Support_Requests
                SET assigned_to = %s, updated_at = NOW()
                WHERE id = %s
            """, (assigned_to, request_id))
            return cursor.rowcount > 0

    @staticmethod
    def get_all_support_requests(status_filter: Optional[str] = None,
                                 assigned_filter: Optional[int] = None,
                                 priority_filter: Optional[str] = None,
                                 issue_type_filter: Optional[str] = None) -> List[Dict]:
        #Get all support requests with optional filters (for support staff)
        with get_cursor() as cursor:
            query = """
                SELECT
                    sr.id,
                    sr.issue_type,
                    sr.subject,
                    sr.status,
                    sr.priority,
                    sr.created_at,
                    sr.updated_at,
                    sr.assigned_to,
                    u.first_name,
                    u.last_name,
                    u.email,
                    assigned.first_name AS assigned_first_name,
                    assigned.last_name AS assigned_last_name
                FROM Support_Requests sr
                INNER JOIN Users u ON sr.user_id = u.id
                LEFT JOIN Users assigned ON sr.assigned_to = assigned.id
                WHERE 1=1
            """
            params = []

            if status_filter:
                query += " AND sr.status = %s"
                params.append(status_filter)

            if assigned_filter:
                query += " AND sr.assigned_to = %s"
                params.append(assigned_filter)

            if priority_filter:
                query += " AND sr.priority = %s"
                params.append(priority_filter)

            if issue_type_filter:
                query += " AND sr.issue_type = %s"
                params.append(issue_type_filter)

            query += " ORDER BY sr.created_at DESC"

            cursor.execute(query, params)
            return cursor.fetchall()

    @staticmethod
    def get_user_participation_history(user_id: int) -> List[Dict]:
        #Get user's event participation history
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    e.id AS event_id,
                    e.name AS event_name,
                    e.datetime AS event_datetime,
                    ep.status,
                    er.total_seconds,
                    er.start_time,
                    er.end_time
                FROM Event_Participants ep
                INNER JOIN Events e ON ep.event_id = e.id
                LEFT JOIN Event_Results er ON ep.event_id = er.event_id AND ep.user_id = er.user_id
                WHERE ep.user_id = %s
                ORDER BY e.datetime DESC
                LIMIT 10
            """, (user_id,))
            return cursor.fetchall()

    @staticmethod
    def get_user_volunteer_history(user_id: int) -> List[Dict]:
        #Get user's volunteer task history
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    e.id AS event_id,
                    e.name AS event_name,
                    e.datetime AS event_datetime,
                    vt.name AS task_name,
                    vt.description AS task_description
                FROM Event_Task_Assignments eta
                INNER JOIN Events e ON eta.event_id = e.id
                INNER JOIN Volunteer_Tasks vt ON eta.task_id = vt.id
                WHERE eta.user_id = %s
                ORDER BY e.datetime DESC
                LIMIT 10
            """, (user_id,))
            return cursor.fetchall()

    @staticmethod
    def take_request(request_id: int, user_id: int) -> bool:
        #Take ownership of a request (assigns to user and changes status to open)
        with get_cursor() as cursor:
            cursor.execute("""
                UPDATE Support_Requests
                SET assigned_to = %s, status = 'open', updated_at = NOW()
                WHERE id = %s AND status = 'new' AND assigned_to IS NULL
            """, (user_id, request_id))
            return cursor.rowcount > 0

    @staticmethod
    def drop_request(request_id: int) -> bool:
        #Drop ownership of a request (unassigns but keeps current status)
        with get_cursor() as cursor:
            cursor.execute("""
                UPDATE Support_Requests
                SET assigned_to = NULL, updated_at = NOW()
                WHERE id = %s
            """, (request_id,))
            return cursor.rowcount > 0

    @staticmethod
    def get_support_staff_list() -> List[Dict]:
        #Get all users with support staff roles (super_admin or support_technician)
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT id, first_name, last_name, email, global_role
                FROM Users
                WHERE global_role IN ('super_admin', 'support_technician')
                  AND status = 'active'
                ORDER BY first_name, last_name
            """)
            return cursor.fetchall()

    @staticmethod
    def log_status_change(request_id: int, changed_by: int, old_status: str,
                         new_status: str, comment_id: Optional[int] = None) -> int:
        #Log a status change to the audit trail
        with get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO Support_Request_Status_Changes
                (request_id, changed_by, old_status, new_status, comment_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (request_id, changed_by, old_status, new_status, comment_id))
            return cursor.lastrowid

    @staticmethod
    def update_status_with_log(request_id: int, new_status: str, changed_by: int,
                               comment_id: Optional[int] = None) -> bool:
        #Update status and log the change in a single transaction
        with get_cursor() as cursor:
            # Get current status first
            cursor.execute("SELECT status FROM Support_Requests WHERE id = %s", (request_id,))
            result = cursor.fetchone()
            if not result:
                return False

            old_status = result['status']

            # Update the status
            cursor.execute("""
                UPDATE Support_Requests
                SET status = %s, updated_at = NOW()
                WHERE id = %s
            """, (new_status, request_id))

            if cursor.rowcount > 0:
                # Log the status change
                cursor.execute("""
                    INSERT INTO Support_Request_Status_Changes
                    (request_id, changed_by, old_status, new_status, comment_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (request_id, changed_by, old_status, new_status, comment_id))
                return True
            return False

    @staticmethod
    def reopen_request(request_id: int, changed_by: int) -> bool:
        #Reopen a resolved request (changes status from resolved to open)
        with get_cursor() as cursor:
            # Get current status
            cursor.execute("SELECT status FROM Support_Requests WHERE id = %s", (request_id,))
            result = cursor.fetchone()
            if not result or result['status'] != 'resolved':
                return False

            # Update status to open
            cursor.execute("""
                UPDATE Support_Requests
                SET status = 'open', updated_at = NOW()
                WHERE id = %s AND status = 'resolved'
            """, (request_id,))

            if cursor.rowcount > 0:
                # Log the status change
                cursor.execute("""
                    INSERT INTO Support_Request_Status_Changes
                    (request_id, changed_by, old_status, new_status, comment_id)
                    VALUES (%s, %s, 'resolved', 'open', NULL)
                """, (request_id, changed_by))
                return True
            return False

    @staticmethod
    def get_status_history(request_id: int) -> List[Dict]:
        #Get the status change history for a request
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    sc.id,
                    sc.old_status,
                    sc.new_status,
                    sc.changed_at,
                    sc.comment_id,
                    u.first_name,
                    u.last_name,
                    c.comment
                FROM Support_Request_Status_Changes sc
                INNER JOIN Users u ON sc.changed_by = u.id
                LEFT JOIN Support_Request_Comments c ON sc.comment_id = c.id
                WHERE sc.request_id = %s
                ORDER BY sc.changed_at ASC
            """, (request_id,))
            return cursor.fetchall()
        
    @staticmethod
    def create_notification(user_id: int, notification_type: str,
                          reference_id: int, message: str) -> int:
        #Create a new notification for a user
        with get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO Notifications (user_id, type, reference_id, message)
                VALUES (%s, %s, %s, %s)
            """, (user_id, notification_type, reference_id, message))
            return cursor.lastrowid

    @staticmethod
    def get_user_notifications(user_id: int, unread_only: bool = False) -> List[Dict]:
        #Get notifications for a user
        with get_cursor() as cursor:
            query = """
                SELECT
                    n.id,
                    n.type,
                    n.reference_id,
                    n.message,
                    n.is_read,
                    n.created_at,
                    sr.subject AS request_subject
                FROM Notifications n
                LEFT JOIN Support_Requests sr ON n.reference_id = sr.id
                WHERE n.user_id = %s
            """
            params = [user_id]

            if unread_only:
                query += " AND n.is_read = FALSE"

            query += " ORDER BY n.created_at DESC"

            cursor.execute(query, params)
            return cursor.fetchall()

    @staticmethod
    def mark_notification_read(notification_id: int, user_id: int) -> bool:
        #Mark a notification as read
        with get_cursor() as cursor:
            cursor.execute("""
                UPDATE Notifications
                SET is_read = TRUE
                WHERE id = %s AND user_id = %s
            """, (notification_id, user_id))
            return cursor.rowcount > 0

    @staticmethod
    def get_unread_notification_count(user_id: int) -> int:
        #Get count of unread notifications for a user
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM Notifications
                WHERE user_id = %s AND is_read = FALSE
            """, (user_id,))
            result = cursor.fetchone()
            return result['count'] if result else 0

    @staticmethod
    def mark_all_notifications_read(user_id: int) -> bool:
        #Mark all notifications as read for a user
        with get_cursor() as cursor:
            cursor.execute("""
                UPDATE Notifications
                SET is_read = TRUE
                WHERE user_id = %s AND is_read = FALSE
            """, (user_id,))
            return cursor.rowcount > 0
