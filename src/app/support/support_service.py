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
                               is_staff_reply: bool = False) -> bool:
        #Add a comment to a support request and update status if needed
        
        if not comment or not comment.strip():
            raise ValueError("Comment cannot be empty")

        # Get the request to check status
        request = SupportRepository.get_support_request_by_id(request_id)

        if not request:
            raise ValueError("Support request not found")

        if request['status'] == 'resolved':
            raise ValueError("Cannot add comments to resolved requests")

        # Add the comment
        comment_id = SupportRepository.add_comment(
            request_id, user_id, comment.strip(), is_staff_reply
        )

        # If this is a new request and someone is commenting, update to open
        if request['status'] == 'new' and is_staff_reply:
            SupportRepository.update_request_status(request_id, 'open')

        return comment_id > 0

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
