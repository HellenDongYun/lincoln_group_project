from typing import Optional, List, Dict
from src.app.support.support_repository import SupportRepository

class SupportService:    

    def __init__(self):
        self.repository = SupportRepository()

    @staticmethod
    def create_support_request(user_id: int, issue_type: str, subject: str,
                               description: str, screenshot_path: Optional[str] = None,
                               priority: str = 'medium') -> int:
        #Create a new support request, then return its ID

        if not subject or not subject.strip():
            raise ValueError("Subject is required")

        if not description or not description.strip():
            raise ValueError("Description is required")

        valid_issue_types = ['technical', 'account', 'event', 'group', 'volunteer', 'bug', 'other']
        if issue_type not in valid_issue_types:
            raise ValueError(f"Invalid issue type. Must be one of: {', '.join(valid_issue_types)}")

        valid_priorities = ['low', 'medium', 'high']
        if priority not in valid_priorities:
            raise ValueError(f"Invalid priority. Must be one of: {', '.join(valid_priorities)}")

        return SupportRepository.create_support_request(
            user_id, issue_type, subject.strip(), description.strip(), screenshot_path, priority
        )

    @staticmethod
    def get_user_requests(user_id: int) -> List[Dict]:
        #Get all support requests for a user
        return SupportRepository.get_user_support_requests(user_id)

    @staticmethod
    def get_request_details(request_id: int, user_id: Optional[int] = None) -> Optional[Dict]:
        #Get support request details If user_id is provided, verify the user owns the request or is support staff

        request = SupportRepository.get_support_request_by_id(request_id)

        if not request:
            return None

        # If user_id provided, verify access (will be checked in controller with role)
        if user_id and request['user_id'] != user_id:
            # This check will be combined with role check in controller
            pass

        # Get comments for this request
        comments = SupportRepository.get_request_comments(request_id)
        request['comments'] = comments

        # Get user participation and volunteer history for support staff
        request['participation_history'] = SupportRepository.get_user_participation_history(request['user_id'])
        request['volunteer_history'] = SupportRepository.get_user_volunteer_history(request['user_id'])

        return request

    @staticmethod
    def add_comment_to_request(request_id: int, user_id: int, comment: str,
                               is_staff_reply: bool = False) -> int:
        #Add a comment to a support request and update status if needed

        if not comment or not comment.strip():
            raise ValueError("Comment cannot be empty")

        # Get the request to check status
        request = SupportRepository.get_support_request_by_id(request_id)

        if not request:
            raise ValueError("Support request not found")

        # Regular users cannot comment on resolved or cancelled requests (only staff can comment on resolved)
        if request['status'] == 'resolved' and not is_staff_reply:
            raise ValueError("Cannot add comments to resolved requests. Please reopen the request first.")

        # Nobody can comment on cancelled requests
        if request['status'] == 'cancelled':
            raise ValueError("Cannot add comments to cancelled requests.")

        # Add the comment
        comment_id = SupportRepository.add_comment(
            request_id, user_id, comment.strip(), is_staff_reply
        )

        # If this is a new request and staff is commenting, update to open
        if request['status'] == 'new' and is_staff_reply:
            SupportRepository.update_request_status(request_id, 'open')

        return comment_id  # Return comment_id for use in AC6 (resolving with comment)

    @staticmethod
    def update_status(request_id: int, new_status: str) -> bool:
        #Update the status of a support request

        valid_statuses = ['new', 'open', 'stalled', 'resolved']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        # Get current request
        request = SupportRepository.get_support_request_by_id(request_id)

        if not request:
            raise ValueError("Support request not found")

        # Prevent reverting to 'new' from 'open'
        if request['status'] == 'open' and new_status == 'new':
            raise ValueError("Cannot revert status from 'open' to 'new'")

        return SupportRepository.update_request_status(request_id, new_status)

    @staticmethod
    def assign_request(request_id: int, assigned_to: Optional[int]) -> bool:
        #Assign a request to a support staff member
        return SupportRepository.assign_request(request_id, assigned_to)

    @staticmethod
    def get_all_requests(status_filter: Optional[str] = None,
                        assigned_filter: Optional[int] = None,
                        priority_filter: Optional[str] = None,
                        issue_type_filter: Optional[str] = None) -> List[Dict]:
        #Get all support requests with filters (for support staff)
        return SupportRepository.get_all_support_requests(
            status_filter, assigned_filter, priority_filter, issue_type_filter
        )

    @staticmethod
    def can_user_access_request(request_id: int, user_id: int, is_staff: bool) -> bool:
        #Check if a user can access a support request
        request = SupportRepository.get_support_request_by_id(request_id)

        if not request:
            return False

        # Staff can access all requests
        if is_staff:
            return True

        # Users can only access their own requests
        return request['user_id'] == user_id
    
    @staticmethod
    def take_request(request_id: int, user_id: int) -> bool:
        #Take ownership of a request - can take unassigned or reassign from others

        # Get the request
        request = SupportRepository.get_support_request_by_id(request_id)
        if not request:
            raise ValueError("Support request not found")

        # Cannot take your own request
        if request['assigned_to'] == user_id:
            raise ValueError("This request is already assigned to you")

        # Cannot take resolved requests
        if request['status'] == 'resolved':
            raise ValueError("Cannot take resolved requests. Please reopen first.")

        previous_assignee = request['assigned_to']
        old_status = request['status']

        # Assign to user and update status to 'open' if currently 'new'
        if request['status'] == 'new':
            success = SupportRepository.take_request(request_id, user_id)
            if success:
                # Log the status change from new to open
                SupportRepository.log_status_change(
                    request_id, user_id, 'new', 'open', None
                )
        else:
            # For non-new requests, just reassign without changing status
            success = SupportRepository.assign_request(request_id, user_id)

        if success:
            # Get staff name for notification
            from src.app.user.user_repository import UserRepository
            user_repo = UserRepository()
            staff = user_repo.get_user_by_id(user_id)
            staff_name = f"{staff['first_name']} {staff['last_name']}" if staff else "Support Staff"

            # Notify request creator
            SupportRepository.create_notification(
                request['user_id'],
                'request_assigned',
                request_id,
                f"Your support request #{request_id} has been taken by {staff_name}"
            )

            # If reassigning from another staff member, notify them
            if previous_assignee and previous_assignee != user_id:
                SupportRepository.create_notification(
                    previous_assignee,
                    'request_status_changed',
                    request_id,
                    f"Request #{request_id} has been taken by {staff_name}"
                )

        return success

    @staticmethod
    def drop_request(request_id: int, user_id: int) -> bool:
        #Drop ownership of a request (AC3)

        # Get the request
        request = SupportRepository.get_support_request_by_id(request_id)
        if not request:
            raise ValueError("Support request not found")

        # Validate user is the current owner
        if request['assigned_to'] != user_id:
            raise ValueError("You can only drop requests assigned to you")

        # Cannot drop resolved requests
        if request['status'] == 'resolved':
            raise ValueError("Cannot drop resolved requests")

        # Drop the request
        success = SupportRepository.drop_request(request_id)

        if success:
            # Notify request creator
            SupportRepository.create_notification(
                request['user_id'],
                'request_dropped',
                request_id,
                f"Support request #{request_id} has been unassigned and returned to the queue"
            )

        return success

    @staticmethod
    def assign_to_staff(request_id: int, assigned_to: int, assigned_by: int) -> bool:
        #Assign request to a staff member (AC2)

        # Validate assigned_to is support staff
        from src.app.user.user_repository import UserRepository
        user_repo = UserRepository()
        user = user_repo.get_user_by_id(assigned_to)
        if not user or user['global_role'] not in ('super_admin', 'support_technician'):
            raise ValueError("Can only assign to support staff")

        # Get the request to check previous assignment
        request = SupportRepository.get_support_request_by_id(request_id)
        if not request:
            raise ValueError("Support request not found")

        previous_assignee = request['assigned_to']

        # Assign the request
        success = SupportRepository.assign_request(request_id, assigned_to)

        if success:
            # Get staff name
            staff_name = f"{user['first_name']} {user['last_name']}"

            # Notify newly assigned staff
            SupportRepository.create_notification(
                assigned_to,
                'request_assigned',
                request_id,
                f"You have been assigned support request #{request_id}: {request['subject']}"
            )

            # If previously assigned to someone else, notify them
            if previous_assignee and previous_assignee != assigned_to:
                SupportRepository.create_notification(
                    previous_assignee,
                    'request_status_changed',
                    request_id,
                    f"Request #{request_id} has been reassigned to {staff_name}"
                )

        return success

    @staticmethod
    def update_status_with_comment(request_id: int, new_status: str, changed_by: int,
                                   comment_id: Optional[int] = None) -> bool:
        #Update request status with validation (AC5, AC6)

        # Validate status
        valid_statuses = ['new', 'open', 'stalled', 'resolved']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        # Get current request
        request = SupportRepository.get_support_request_by_id(request_id)
        if not request:
            raise ValueError("Support request not found")

        # AC5: Cannot revert from 'open' to 'new'
        if request['status'] == 'open' and new_status == 'new':
            raise ValueError("Cannot revert status from 'open' to 'new'")

        # AC6: Cannot change to 'resolved' without comment
        if new_status == 'resolved' and not comment_id:
            raise ValueError("A comment is required when marking a request as resolved")

        # Update status with log
        success = SupportRepository.update_status_with_log(
            request_id, new_status, changed_by, comment_id
        )

        if success:
            # AC9: Notify request creator of status change
            SupportRepository.create_notification(
                request['user_id'],
                'request_status_changed',
                request_id,
                f"Your support request #{request_id} status changed to {new_status.title()}"
            )

            # Also notify assigned staff if different from changer
            if request['assigned_to'] and request['assigned_to'] != changed_by:
                SupportRepository.create_notification(
                    request['assigned_to'],
                    'request_status_changed',
                    request_id,
                    f"Support request #{request_id} status changed to {new_status.title()}"
                )

        return success

    @staticmethod
    def reopen_request(request_id: int, user_id: int) -> bool:
        #Reopen a resolved request (AC8)

        # Get the request
        request = SupportRepository.get_support_request_by_id(request_id)
        if not request:
            raise ValueError("Support request not found")

        # Validate status is resolved
        if request['status'] != 'resolved':
            raise ValueError("Can only reopen resolved requests")

        # Validate user is request creator or support staff
        from src.app.user.user_repository import UserRepository
        user_repo = UserRepository()
        user = user_repo.get_user_by_id(user_id)
        is_staff = user and user['global_role'] in ('super_admin', 'support_technician')

        if request['user_id'] != user_id and not is_staff:
            raise ValueError("Only request creator or support staff can reopen requests")

        # Reopen the request
        success = SupportRepository.reopen_request(request_id, user_id)

        if success:
            # Get user name for notification
            user_name = f"{user['first_name']} {user['last_name']}" if user else "User"

            # Notify assigned staff (if any)
            if request['assigned_to']:
                SupportRepository.create_notification(
                    request['assigned_to'],
                    'request_status_changed',
                    request_id,
                    f"Request #{request_id} has been reopened by {user_name}"
                )

        return success

    @staticmethod
    def get_staff_list() -> List[Dict]:
        #Get list of support staff for assignment dropdown
        return SupportRepository.get_support_staff_list()

    @staticmethod
    def get_notifications(user_id: int, unread_only: bool = False) -> List[Dict]:
        #Get notifications for a user
        return SupportRepository.get_user_notifications(user_id, unread_only)

    @staticmethod
    def mark_notification_read(notification_id: int, user_id: int) -> bool:
        #Mark a notification as read
        return SupportRepository.mark_notification_read(notification_id, user_id)

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        #Get count of unread notifications
        return SupportRepository.get_unread_notification_count(user_id)

    @staticmethod
    def close_user_request(request_id: int, user_id: int) -> bool:
        #Allow users to close their own requests when in new or open status

        # Get the request
        request = SupportRepository.get_support_request_by_id(request_id)
        if not request:
            raise ValueError("Support request not found")

        # Verify user is the request creator
        if request['user_id'] != user_id:
            raise ValueError("You can only close your own support requests")

        # Can only close requests that are 'new' (unassigned) or 'open'
        if request['status'] not in ('new', 'open'):
            if request['status'] == 'cancelled':
                raise ValueError("This request is already closed")
            elif request['status'] == 'resolved':
                raise ValueError("Cannot close a resolved request")
            elif request['status'] == 'stalled':
                raise ValueError("Cannot close a stalled request. Please wait for staff response or contact support.")
            else:
                raise ValueError(f"Cannot close request with status: {request['status']}")

        old_status = request['status']

        # Update status to cancelled (displayed as "Closed by User")
        success = SupportRepository.update_status_with_log(
            request_id, 'cancelled', user_id, None
        )

        if success:
            # Notify assigned staff if any
            if request['assigned_to']:
                from src.app.user.user_repository import UserRepository
                user_repo = UserRepository()
                user = user_repo.get_user_by_id(user_id)
                user_name = f"{user['first_name']} {user['last_name']}" if user else "User"

                SupportRepository.create_notification(
                    request['assigned_to'],
                    'request_status_changed',
                    request_id,
                    f"Request #{request_id} has been closed by {user_name} (request creator)"
                )

        return success
