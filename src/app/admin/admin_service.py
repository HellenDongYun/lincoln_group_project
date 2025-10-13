import math
from src.app.common.db.cursor import get_cursor
from src.app.admin.admin import Admin
from src.app.admin.admin_repository import AdminRepository
from src.app.group.group_repository import GroupRepository
from src.app.user.user import GroupVisibility, GroupStatus


class AdminService:

    def __init__(self):
        self.repository = AdminRepository()

    def get_admin_by_admin_id(self, admin_id: int) -> Admin:
        row = self.repository.get_admin_by_admin_id(admin_id)
        return Admin(**row) if row else None
    
    @staticmethod
    def get_upcoming_events_with_volunteers(event_filters=None, limit=5):
        """Get upcoming events with their volunteer requirements"""
        return AdminRepository.fetch_upcoming_events_with_volunteers(event_filters, limit)
    
    
    
    @staticmethod
    def get_events(filters):
        name = filters["name"]
        town = filters["town"]
        order = filters["order"]
        page = filters["page"]
        per_page = filters["per_page"]
        offset = (page - 1) * per_page

        # 1. check the total records
        total_records = AdminRepository.count_events(name, town)
        total_pages = math.ceil(total_records / per_page) if total_records else 1

        # 2. pagination data
        events = AdminRepository.fetch_events(name, town, order, per_page, offset)
        
        # 3. Add capacity warnings for events near capacity (80% or more)
        events_with_warnings = []
        for event in events:
            event_dict = dict(event)
            participant_count = event_dict.get('participant_count', 0)
            max_participants = event_dict.get('max_participants', 0)
            
            if max_participants > 0:
                capacity_percentage = (participant_count / max_participants) * 100
                event_dict['capacity_percentage'] = capacity_percentage
                event_dict['near_capacity'] = capacity_percentage >= 80
                event_dict['at_capacity'] = capacity_percentage >= 100
            else:
                event_dict['capacity_percentage'] = 0
                event_dict['near_capacity'] = False
                event_dict['at_capacity'] = False
                
            events_with_warnings.append(event_dict)

        return events_with_warnings, page, total_pages
    
    @staticmethod
    def delete_event(event_id: int):
        AdminRepository.delete_event(event_id)
    @staticmethod
    def get_event_details(event_id):
        event = AdminRepository.get_event_by_id(event_id)
        volunteer_roles = AdminRepository.get_volunteer_roles(event_id)
        participants = AdminRepository.get_event_participants_by_event_id(event_id)
        participant_count = AdminRepository.count_event_participants(event_id)
        volunteer_total = AdminRepository.sum_volunteer_spots(event_id)

        return {
            "event": event,
            "volunteer_roles": volunteer_roles,
            "participants": participants,
            "event_register_user_count": participant_count,
            "volunteer_total_amount": volunteer_total
        }
        
        
    @staticmethod
    def get_event_name(event_id):
        return AdminRepository.fetch_event_name(event_id)

    @staticmethod
    def fetch_all_volunteer_roles():
        return AdminRepository.fetch_all_roles()

    @staticmethod
    def get_assigned_roles(event_id):
        return AdminRepository.fetch_assigned_roles(event_id)

    @staticmethod
    def remove_volunteer_role(event_id, role_id):
        AdminRepository.delete_role_assignment(event_id, role_id)

    @staticmethod
    def upsert_volunteer_role(event_id, role_id, spots):
        AdminRepository.upsert_role_assignment(event_id, role_id, spots)
    

    
    @staticmethod
    def get_all_volunteer_roles(filters: dict, page: int = 1, per_page: int = 10):
        rows, total_count = AdminRepository.get_all_volunteer_roles(filters, page, per_page)
        total_pages = math.ceil(total_count / per_page)
        return {
            "volunteers": rows,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "filters": filters
        } 
        
    @staticmethod
    def set_user_status(user_id: int, event_id: int, status: str) -> str:
        updated_rows = AdminRepository.update_participant_status(user_id, event_id, status)
        if updated_rows == 0:
            raise ValueError("User or event not found")
        
        return status
    
    @staticmethod
    def get_event_participants(full_name=None, role=None, status=None, page=1, per_page=10):
        offset = (page - 1) * per_page
        return AdminRepository.get_event_participants_filtered(
            full_name=full_name,
            role=role,
            status=status,
            limit=per_page,
            offset=offset)
            
    @staticmethod
    def count_event_participants(full_name=None, role=None, status=None):
        return AdminRepository.count_event_participants_filtered(
            full_name=full_name,
            role=role,
            status=status
        )
    
    @staticmethod
    def get_results():
        return AdminRepository.get_results()
    
    @staticmethod
    def update_user_role(user_id, new_role):
        """Update a user's role"""
        return AdminRepository.update_user_role(user_id, new_role)
    
    @staticmethod
    def update_user_status(user_id, new_status):
        """Update a user's status"""
        return AdminRepository.update_user_status(user_id, new_status)
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user details by ID"""
        return AdminRepository.get_user_by_id(user_id)
    
    @staticmethod
    def get_users_for_role_management(page=1, per_page=10, search_name=None, search_role=None):
        """Get users with pagination for role management"""
        users, total_count = AdminRepository.get_all_users_simple(page, per_page, search_name, search_role)
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1

        return {
            'users': users,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_count': total_count
        }

    @staticmethod
    def get_group_overview(filters=None, limit=6):
        rows = AdminRepository.fetch_group_overview(filters, limit)
        overview = []
        for row in rows:
            managers = []
            raw_names = row.get('manager_names')
            if raw_names:
                managers = [name for name in raw_names.split('|') if name]
            overview.append({
                'group_id': row['group_id'],
                'name': row['name'],
                'description': row.get('description'),
                'town': row.get('town'),
                'visibility': row.get('visibility'),
                'status': row.get('status'),
                'member_count': row.get('member_count', 0),
                'manager_count': row.get('manager_count', 0),
                'manager_names': managers,
                'upcoming_events_count': row.get('upcoming_events_count', 0)
            })
        return overview

    @staticmethod
    def get_pending_group_applications():
        return AdminRepository.fetch_pending_group_applications()

    @staticmethod
    def get_group_filter_options():
        options = AdminRepository.fetch_group_filter_options()
        return {
            'visibilities': [visibility.value for visibility in GroupVisibility],
            'statuses': [status.value for status in GroupStatus],
            'towns': options.get('towns', [])
        }

    @staticmethod
    def get_event_filter_options():
        return AdminRepository.fetch_event_filter_options()

    @staticmethod
    def get_monitoring_metrics(timeframe_days=30):
        return AdminRepository.fetch_monitoring_metrics(timeframe_days)

    @staticmethod
    def assign_group_manager(group_id, manager_email):
        if not manager_email:
            raise ValueError("Manager email is required")

        email = manager_email.strip().lower()
        if not email:
            raise ValueError("Manager email is required")

        user = AdminRepository.find_user_by_email(email)
        if not user:
            raise ValueError("No user found with that email address")

        with get_cursor() as cursor:
            GroupRepository.add_group_member(cursor, group_id, user['id'], group_role='manager')

            return {
                'user_id': user['id'],
                'full_name': f"{user['first_name']} {user['last_name']}",
                'email': user['email']
            }

    @staticmethod
    def create_group(name, description, town, visibility, created_by, manager_email=None):
        if not name:
            raise ValueError("Group name is required")
        if not town:
            raise ValueError("Town or region is required")
        if visibility not in [v.value for v in GroupVisibility]:
            raise ValueError("Invalid visibility option selected")
        if not created_by:
            raise ValueError("Unable to determine creator for the group")

        manager_email_normalized = manager_email.strip().lower() if manager_email else None
        manager_user = AdminRepository.find_user_by_email(manager_email_normalized) if manager_email_normalized else None

        with get_cursor() as cursor:
            group_id = GroupRepository.create_group(cursor, name, description, town, visibility, created_by)

            manager_info = None
            manager_warning = None
            if manager_email_normalized:
                if manager_user:
                    GroupRepository.add_group_member(cursor, group_id, manager_user['id'], group_role='manager')
                    manager_info = {
                        'user_id': manager_user['id'],
                        'full_name': f"{manager_user['first_name']} {manager_user['last_name']}",
                        'email': manager_user['email']
                    }
                else:
                    manager_warning = "Manager email not found; group created without an assigned manager."

            return {
                'group_id': group_id,
                'manager': manager_info,
                'manager_warning': manager_warning
            }