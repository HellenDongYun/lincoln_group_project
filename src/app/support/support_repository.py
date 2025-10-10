from src.app.common.db.cursor import get_cursor
from typing import Optional, List, Dict


class SupportRepository:
    """Repository for handling support request database operations"""

    @staticmethod
    def create_support_request(user_id: int, issue_type: str, subject: str,
                               description: str, screenshot_path: Optional[str] = None,
                               priority: str = 'medium') -> int:
        """Create a new support request and return its ID"""
        with get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO Support_Requests
                (user_id, issue_type, subject, description, screenshot_path, priority, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'new')
            """, (user_id, issue_type, subject, description, screenshot_path, priority))
            return cursor.lastrowid

    @staticmethod
    def get_user_support_requests(user_id: int) -> List[Dict]:
        """Get all support requests for a specific user"""
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
        """Get a specific support request by ID"""
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
        """Get all comments for a support request"""
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
                ORDER BY c.created_at ASC
            """, (request_id,))
            return cursor.fetchall()

    @staticmethod
    def add_comment(request_id: int, user_id: int, comment: str,
                    is_staff_reply: bool = False) -> int:
        """Add a comment to a support request"""
        with get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO Support_Request_Comments
                (request_id, user_id, comment, is_staff_reply)
                VALUES (%s, %s, %s, %s)
            """, (request_id, user_id, comment, is_staff_reply))
            return cursor.lastrowid

    @staticmethod
    def update_request_status(request_id: int, new_status: str) -> bool:
        """Update the status of a support request"""
        with get_cursor() as cursor:
            cursor.execute("""
                UPDATE Support_Requests
                SET status = %s, updated_at = NOW()
                WHERE id = %s
            """, (new_status, request_id))
            return cursor.rowcount > 0

    @staticmethod
    def assign_request(request_id: int, assigned_to: Optional[int]) -> bool:
        """Assign a support request to a staff member"""
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
                                 priority_filter: Optional[str] = None) -> List[Dict]:
        """Get all support requests with optional filters (for support staff)"""
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

            query += " ORDER BY sr.created_at DESC"

            cursor.execute(query, params)
            return cursor.fetchall()
