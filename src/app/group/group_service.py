from src.app.common.db.cursor import get_cursor
from src.app.group.group_repository import GroupRepository
from src.app.user.user import CommunityGroup, GroupMembership, GroupApplication


class GroupService:
    
    @staticmethod
    def get_all_groups(visibility_filter=None, town_filter=None, page=1, per_page=10):
        """Get paginated list of groups"""
        offset = (page - 1) * per_page
        
        with get_cursor() as cursor:
            groups = GroupRepository.get_all_groups(
                cursor, visibility_filter, town_filter, per_page, offset
            )
            
            # Get total count for pagination
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM Community_Groups g 
                WHERE (%s IS NULL OR g.visibility = %s) 
                AND (%s IS NULL OR g.town = %s)
            """, (visibility_filter, visibility_filter, town_filter, town_filter))
            
            total_count = cursor.fetchone()['total']
            total_pages = (total_count + per_page - 1) // per_page
            
            return {
                'groups': groups,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'total_count': total_count
            }

    @staticmethod
    def get_group_by_id(group_id):
        """Get a specific group with its details"""
        with get_cursor() as cursor:
            return GroupRepository.get_group_by_id(cursor, group_id)

    @staticmethod
    def create_group(name, description, town, visibility, join_type, created_by):
        """Create a new group"""
        with get_cursor() as cursor:
            group_id = GroupRepository.create_group(
                cursor, name, description, town, visibility, join_type, created_by
            )
            # Add creator as manager
            GroupRepository.add_group_member(cursor, group_id, created_by, 'manager')
            return group_id

    @staticmethod
    def get_user_groups(user_id):
        """Get all groups a user belongs to"""
        with get_cursor() as cursor:
            return GroupRepository.get_user_groups(cursor, user_id)

    @staticmethod
    def get_group_members(group_id):
        """Get all members of a group"""
        with get_cursor() as cursor:
            return GroupRepository.get_group_members(cursor, group_id)

    @staticmethod
    def add_member_to_group(group_id, user_id, role='member'):
        """Add a user to a group"""
        with get_cursor() as cursor:
            return GroupRepository.add_group_member(cursor, group_id, user_id, role)

    @staticmethod
    def update_member_role(group_id, user_id, new_role):
        """Update a member's role in a group"""
        with get_cursor() as cursor:
            return GroupRepository.update_member_role(cursor, group_id, user_id, new_role)

    @staticmethod
    def remove_member_from_group(group_id, user_id):
        """Remove a member from a group"""
        with get_cursor() as cursor:
            return GroupRepository.remove_group_member(cursor, group_id, user_id)

    @staticmethod
    def is_group_manager(group_id, user_id):
        """Check if user is a manager of the group"""
        with get_cursor() as cursor:
            return GroupRepository.is_group_manager(cursor, group_id, user_id)

    @staticmethod
    def is_group_member(group_id, user_id):
        """Check if user is a member of the group"""
        with get_cursor() as cursor:
            return GroupRepository.is_group_member(cursor, group_id, user_id)

    @staticmethod
    def can_user_manage_group(group_id, user_id, is_super_admin=False):
        """Check if user can manage the group (super admin or group manager)"""
        if is_super_admin:
            return True
        return GroupService.is_group_manager(group_id, user_id)

    @staticmethod
    def can_user_join_group(group_id, user_id):
        """Check if user can join a group"""
        with get_cursor() as cursor:
            group = GroupRepository.get_group_by_id(cursor, group_id)
            if not group:
                return False
            
            # Can't join if already a member
            if GroupRepository.is_group_member(cursor, group_id, user_id):
                return False
            
            # Can join if group is open
            return group['join_type'] == 'open'

    # Group Applications
    @staticmethod
    def create_group_application(applicant_id, proposed_name, proposed_description, 
                               proposed_town, visibility, join_type):
        """Create a new group application"""
        with get_cursor() as cursor:
            return GroupRepository.create_group_application(
                cursor, applicant_id, proposed_name, proposed_description,
                proposed_town, visibility, join_type
            )

    @staticmethod
    def get_pending_applications():
        """Get all pending group applications for super admin review"""
        with get_cursor() as cursor:
            return GroupRepository.get_pending_applications(cursor)

    @staticmethod
    def get_application_by_id(application_id):
        """Get a specific group application"""
        with get_cursor() as cursor:
            return GroupRepository.get_application_by_id(cursor, application_id)

    @staticmethod
    def approve_group_application(application_id, decision_by):
        """Approve a group application and create the group"""
        with get_cursor() as cursor:
            application = GroupRepository.get_application_by_id(cursor, application_id)
            if not application or application['status'] != 'pending':
                raise ValueError("Application not found or not pending")

            # Update application status
            GroupRepository.update_application_status(cursor, application_id, 'approved', decision_by)
            
            # Create the group
            group_id = GroupRepository.create_group(
                cursor, 
                application['proposed_name'],
                application['proposed_description'],
                application['proposed_town'],
                application['visibility'],
                application['join_type'],
                decision_by  # Super admin creates it
            )
            
            # Add applicant as manager
            GroupRepository.add_group_member(cursor, group_id, application['applicant_id'], 'manager')
            
            return group_id

    @staticmethod
    def reject_group_application(application_id, decision_by):
        """Reject a group application"""
        with get_cursor() as cursor:
            return GroupRepository.update_application_status(cursor, application_id, 'rejected', decision_by)

    @staticmethod
    def get_public_groups_for_discovery(town_filter=None, search_term=None):
        """Get public groups for discovery page"""
        with get_cursor() as cursor:
            return GroupRepository.get_public_groups_for_discovery(cursor, town_filter, search_term)

    @staticmethod
    def get_user_managed_groups(user_id):
        """Get groups where user is a manager"""
        with get_cursor() as cursor:
            groups = GroupRepository.get_user_groups(cursor, user_id)
            return [group for group in groups if group['group_role'] == 'manager']