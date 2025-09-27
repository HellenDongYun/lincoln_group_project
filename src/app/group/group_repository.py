from src.app.common.db.repository import Repository
from src.app.common.db.cursor import get_cursor
from src.app.user.user import CommunityGroup, GroupMembership, GroupApplication, GroupVisibility, GroupJoinType, GroupStatus, GroupRole


class GroupRepository(Repository):
    
    @staticmethod
    def get_all_groups(cursor, visibility_filter=None, town_filter=None, limit=None, offset=0):
        """Get all groups with optional filtering"""
        query = """
            SELECT g.id, g.name, g.description, g.town, g.visibility, g.join_type, g.status, g.created_by,
                   COUNT(gm.user_id) as member_count
            FROM Community_Groups g
            LEFT JOIN Group_Memberships gm ON g.id = gm.group_id AND gm.member_status = 'active'
            WHERE 1=1
        """
        params = []
        
        if visibility_filter:
            query += " AND g.visibility = %s"
            params.append(visibility_filter)
            
        if town_filter:
            query += " AND g.town = %s"
            params.append(town_filter)
            
        query += " GROUP BY g.id, g.name, g.description, g.town, g.visibility, g.join_type, g.status, g.created_by"
        query += " ORDER BY g.name ASC"
        
        if limit:
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
        cursor.execute(query, params)
        return cursor.fetchall()

    @staticmethod
    def get_group_by_id(cursor, group_id):
        """Get a specific group by ID"""
        cursor.execute("""
            SELECT g.id, g.name, g.description, g.town, g.visibility, g.join_type, g.status, g.created_by,
                   u.first_name, u.last_name,
                   COUNT(gm.user_id) as member_count
            FROM Community_Groups g
            JOIN Users u ON g.created_by = u.id
            LEFT JOIN Group_Memberships gm ON g.id = gm.group_id AND gm.member_status = 'active'
            WHERE g.id = %s
            GROUP BY g.id
        """, (group_id,))
        return cursor.fetchone()

    @staticmethod
    def create_group(cursor, name, description, town, visibility, join_type, created_by):
        """Create a new group"""
        cursor.execute("""
            INSERT INTO Community_Groups (name, description, town, visibility, join_type, status, created_by)
            VALUES (%s, %s, %s, %s, %s, 'active', %s)
        """, (name, description, town, visibility, join_type, created_by))
        return cursor.lastrowid

    @staticmethod
    def get_user_groups(cursor, user_id):
        """Get all groups a user is a member of"""
        cursor.execute("""
            SELECT g.id, g.name, g.description, g.town, g.visibility, g.join_type, g.status,
                   gm.group_role, gm.member_status
            FROM Community_Groups g
            JOIN Group_Memberships gm ON g.id = gm.group_id
            WHERE gm.user_id = %s AND gm.member_status = 'active'
            ORDER BY g.name ASC
        """, (user_id,))
        return cursor.fetchall()

    @staticmethod
    def get_group_members(cursor, group_id):
        """Get all members of a group"""
        cursor.execute("""
            SELECT u.id, u.first_name, u.last_name, u.email, u.town,
                   gm.group_role, gm.member_status
            FROM Users u
            JOIN Group_Memberships gm ON u.id = gm.user_id
            WHERE gm.group_id = %s AND gm.member_status = 'active'
            ORDER BY gm.group_role DESC, u.first_name ASC
        """, (group_id,))
        return cursor.fetchall()

    @staticmethod
    def add_group_member(cursor, group_id, user_id, group_role='member'):
        """Add a user to a group"""
        cursor.execute("""
            INSERT INTO Group_Memberships (group_id, user_id, group_role, member_status)
            VALUES (%s, %s, %s, 'active')
            ON DUPLICATE KEY UPDATE member_status = 'active', group_role = %s
        """, (group_id, user_id, group_role, group_role))
        return cursor.rowcount

    @staticmethod
    def update_member_role(cursor, group_id, user_id, new_role):
        """Update a member's role in a group"""
        cursor.execute("""
            UPDATE Group_Memberships 
            SET group_role = %s 
            WHERE group_id = %s AND user_id = %s
        """, (new_role, group_id, user_id))
        return cursor.rowcount

    @staticmethod
    def remove_group_member(cursor, group_id, user_id):
        """Remove a user from a group"""
        cursor.execute("""
            UPDATE Group_Memberships 
            SET member_status = 'inactive' 
            WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id))
        return cursor.rowcount

    @staticmethod
    def is_group_manager(cursor, group_id, user_id):
        """Check if a user is a manager of a specific group"""
        cursor.execute("""
            SELECT 1 FROM Group_Memberships 
            WHERE group_id = %s AND user_id = %s 
            AND group_role = 'manager' AND member_status = 'active'
        """, (group_id, user_id))
        return cursor.fetchone() is not None

    @staticmethod
    def is_group_member(cursor, group_id, user_id):
        """Check if a user is a member of a specific group"""
        cursor.execute("""
            SELECT 1 FROM Group_Memberships 
            WHERE group_id = %s AND user_id = %s AND member_status = 'active'
        """, (group_id, user_id))
        return cursor.fetchone() is not None

    @staticmethod
    def update_group_settings(cursor, group_id, visibility, status):
        """Update visibility and status of a group"""
        cursor.execute("""
            UPDATE Community_Groups
            SET visibility = %s, status = %s
            WHERE id = %s
        """, (visibility, status, group_id))
        return cursor.rowcount

    @staticmethod
    def get_group_events(cursor, group_id, include_past=False, limit=None):
        """Fetch events associated with a group"""
        query = """
            SELECT e.id, e.group_id, e.datetime, e.town, e.name, e.event_type,
                   e.description, e.max_participants, e.visibility, e.created_by
            FROM Events e
            WHERE e.group_id = %s
        """
        params = [group_id]

        if not include_past:
            query += " AND e.datetime >= NOW()"

        query += " ORDER BY e.datetime ASC"

        if limit is not None:
            query += " LIMIT %s"
            params.append(limit)

        cursor.execute(query, params)
        return cursor.fetchall()

    # Group Applications
    @staticmethod
    def create_group_application(cursor, applicant_id, proposed_name, proposed_description, 
                               proposed_town, visibility, join_type):
        """Create a new group application"""
        cursor.execute("""
            INSERT INTO Group_Applications 
            (applicant_id, proposed_name, proposed_description, proposed_town, visibility, join_type, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending')
        """, (applicant_id, proposed_name, proposed_description, proposed_town, visibility, join_type))
        return cursor.lastrowid

    @staticmethod
    def get_pending_applications(cursor):
        """Get all pending group applications"""
        cursor.execute("""
            SELECT ga.id, ga.applicant_id, ga.proposed_name, ga.proposed_description, 
                   ga.proposed_town, ga.visibility, ga.join_type, ga.status,
                   u.first_name, u.last_name, u.email
            FROM Group_Applications ga
            JOIN Users u ON ga.applicant_id = u.id
            WHERE ga.status = 'pending'
            ORDER BY ga.id ASC
        """)
        return cursor.fetchall()

    @staticmethod
    def get_application_by_id(cursor, application_id):
        """Get a specific group application"""
        cursor.execute("""
            SELECT ga.*, u.first_name, u.last_name, u.email
            FROM Group_Applications ga
            JOIN Users u ON ga.applicant_id = u.id
            WHERE ga.id = %s
        """, (application_id,))
        return cursor.fetchone()

    @staticmethod
    def update_application_status(cursor, application_id, status, decision_by):
        """Update the status of a group application"""
        cursor.execute("""
            UPDATE Group_Applications 
            SET status = %s, decision_by = %s
            WHERE id = %s
        """, (status, decision_by, application_id))
        return cursor.rowcount

    @staticmethod
    def get_public_groups_for_discovery(cursor, town_filter=None, search_term=None):
        """Get public groups for discovery by visitors and participants"""
        query = """
            SELECT g.id, g.name, g.description, g.town, g.join_type,
                   COUNT(gm.user_id) as member_count,
                   COUNT(CASE WHEN e.datetime > NOW() THEN 1 END) as upcoming_events
            FROM Community_Groups g
            LEFT JOIN Group_Memberships gm ON g.id = gm.group_id AND gm.member_status = 'active'
            LEFT JOIN Events e ON g.id = e.group_id
            WHERE g.visibility = 'public' AND g.status = 'active'
        """
        params = []
        
        if town_filter:
            query += " AND g.town = %s"
            params.append(town_filter)
            
        if search_term:
            query += " AND (g.name LIKE %s OR g.description LIKE %s)"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern])
            
        query += """
            GROUP BY g.id, g.name, g.description, g.town, g.join_type
            ORDER BY upcoming_events DESC, member_count DESC, g.name ASC
        """
        
        cursor.execute(query, params)
        return cursor.fetchall()