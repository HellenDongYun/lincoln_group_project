from src.app.common.db.cursor import get_cursor
from src.app.group.group_repository import GroupRepository
from src.app.event.event import Event
from src.app.user.user import (
    CommunityGroup,
    GroupMembership,
    GroupApplication,
    GroupVisibility,
    GroupStatus,
)


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

            # Can join immediately if group is public
            return group['visibility'] == 'public'

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

    @staticmethod
    def get_group_events(group_id, include_past=False, limit=None):
        """Get events for a specific group"""
        with get_cursor() as cursor:
            return GroupRepository.get_group_events(cursor, group_id, include_past, limit)

    @staticmethod
    def update_group_settings(group_id, visibility, status):
        """Update group visibility and status"""
        with get_cursor() as cursor:
            return GroupRepository.update_group_settings(cursor, group_id, visibility, status)

    @staticmethod

    def search_for_participants(participant_id, search_term=None, location_filter=None,
                              date_filter=None, type_filter=None, sort_by='popularity'):
        """Get search results specifically for participants with join/register context"""
        with get_cursor() as cursor:
            results = GroupRepository.search_groups_and_events_for_participants(
                cursor, participant_id, search_term, location_filter,
                date_filter, type_filter, sort_by
            )

            # Process results to add additional context for participants
            processed_results = []
            for result in results:
                processed_result = dict(result)

                # Determine join/register status and actions available
                if processed_result['result_type'] == 'group':
                    processed_result['can_join'] = GroupService._can_participant_join_group(processed_result)
                    processed_result['join_action'] = GroupService._get_group_join_action(processed_result)
                elif processed_result['result_type'] == 'event':
                    processed_result['can_register'] = GroupService._can_participant_register_for_event(processed_result)
                    processed_result['register_action'] = GroupService._get_event_register_action(processed_result)

                # Format datetime for display
                if processed_result.get('datetime'):
                    processed_result['formatted_datetime'] = processed_result['datetime'].strftime('%Y-%m-%d %H:%M')

                # Calculate available spaces for events
                if processed_result['result_type'] == 'event' and processed_result.get('max_participants'):
                    registered = processed_result.get('registered_participants', 0)
                    processed_result['available_spaces'] = processed_result['max_participants'] - registered

                processed_results.append(processed_result)

            return processed_results

    @staticmethod
    def get_participant_search_filter_options():
        """Get filter options for participant search (locations, event types, etc.)"""
        with get_cursor() as cursor:
            return GroupRepository.get_participant_search_filter_options(cursor)

    @staticmethod
    def _can_participant_join_group(group_result):
        """Helper to determine if participant can join a group"""
        # Already a member
        if group_result.get('participant_group_role'):
            return False

        # Can join if group is public
        if group_result.get('visibility') == 'public':
            return True

        # Private groups require application
        return group_result.get('visibility') == 'private'

    @staticmethod
    def _get_group_join_action(group_result):
        """Helper to get the appropriate join action for a group"""
        if group_result.get('participant_group_role') == 'manager':
            return 'manage'
        elif group_result.get('participant_group_role') == 'member':
            return 'member'
        elif group_result.get('visibility') == 'public':
            return 'join_immediately'  # Public groups = immediate join
        elif group_result.get('visibility') == 'private':
            return 'request_access'    # Private groups = request required
        else:
            return 'closed'

    @staticmethod
    def _can_participant_register_for_event(event_result):
        """Helper to determine if participant can register for an event"""
        # Already registered
        if event_result.get('participant_event_status') == 'registered':
            return False

        # Check if event is full
        if event_result.get('max_participants'):
            registered = event_result.get('registered_participants', 0)
            if registered >= event_result['max_participants']:
                return False

        # Can register if event is in the future
        return True

    @staticmethod
    def _get_event_register_action(event_result):
        """Helper to get the appropriate register action for an event"""
        if event_result.get('participant_event_status') == 'registered':
            return 'registered'
        elif event_result.get('max_participants'):
            registered = event_result.get('registered_participants', 0)
            if registered >= event_result['max_participants']:
                return 'full'

        return 'register'

    # Group Join Request Methods
    @staticmethod
    def get_join_action_for_group(group, user_id):
        """Determine what join action is available for user"""
        with get_cursor() as cursor:
            # Check if already a member
            if GroupRepository.is_group_member(cursor, group['id'], user_id):
                # Check if manager
                if GroupRepository.is_group_manager(cursor, group['id'], user_id):
                    return 'manage'
                else:
                    return 'member'

            # Check if has pending request
            existing_request = GroupRepository.check_existing_join_request(cursor, user_id, group['id'])
            if existing_request:
                return 'request_pending'

            # Determine action based on visibility
            if group['visibility'] == 'public':
                return 'join_immediately'
            elif group['visibility'] == 'private':
                return 'request_access'
            else:
                return 'closed'

    @staticmethod
    def request_to_join_group(user_id, group_id, message=None):
        """Submit request to join private group"""
        with get_cursor() as cursor:
            # Validate group exists and is private
            group = GroupRepository.get_group_by_id(cursor, group_id)
            if not group:
                raise ValueError("Group not found")

            if group['visibility'] != 'private':
                raise ValueError("Only private groups require join requests")

            # Check if already a member
            if GroupRepository.is_group_member(cursor, group_id, user_id):
                raise ValueError("Already a member of this group")

            # Check for existing pending request
            existing_request = GroupRepository.check_existing_join_request(cursor, user_id, group_id)
            if existing_request:
                raise ValueError("You already have a pending request for this group")

            # Create the join request
            return GroupRepository.create_join_request(cursor, user_id, group_id, message)

    @staticmethod
    def get_pending_join_requests(group_id):
        """Get pending join requests for group managers"""
        with get_cursor() as cursor:
            return GroupRepository.get_pending_join_requests(cursor, group_id)

    @staticmethod
    def process_join_request(request_id, action, manager_id):
        """Approve or reject join request"""
        with get_cursor() as cursor:
            # Get request details
            request = GroupRepository.get_join_request_by_id(cursor, request_id)
            if not request or request['status'] != 'pending':
                raise ValueError("Request not found or already processed")

            # Validate manager permissions
            if not GroupRepository.is_group_manager(cursor, request['group_id'], manager_id):
                raise ValueError("Only group managers can process join requests")

            if action == 'approve':
                # Update request status
                GroupRepository.update_join_request_status(cursor, request_id, 'approved', manager_id)
                # Add user to group as member
                GroupRepository.add_group_member(cursor, request['group_id'], request['user_id'], 'member')
                return True
            elif action == 'reject':
                # Update request status
                GroupRepository.update_join_request_status(cursor, request_id, 'rejected', manager_id)
                return True
            else:
                raise ValueError("Invalid action. Must be 'approve' or 'reject'")

    @staticmethod
    def can_user_join_group_enhanced(group_id, user_id):
        """Enhanced version that returns join action details"""
        with get_cursor() as cursor:
            group = GroupRepository.get_group_by_id(cursor, group_id)
            if not group:
                return False, "Group not found"

            action = GroupService.get_join_action_for_group(group, user_id)

            if action in ['join_immediately', 'request_access']:
                return True, action
            else:
                return False, action
