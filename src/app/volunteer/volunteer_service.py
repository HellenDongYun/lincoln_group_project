
from src.app.volunteer.volunteer_repository import VolunteerRepository


class VolunteerService:
    def __init__(self):
        self.volunteer_repository = VolunteerRepository()
    
    def get_available_opportunities(self, volunteer_id=None):
        """Get all volunteer opportunities with available vacancies"""
        return self.volunteer_repository.get_available_opportunities(volunteer_id)
    
    def get_volunteer_roles(self, volunteer_id):
        """Get all roles that a volunteer is currently signed up for (upcoming events only)"""
        return self.volunteer_repository.get_volunteer_roles(volunteer_id)
    
    def get_past_volunteer_roles(self, volunteer_id):
        """Get all past volunteer roles that a volunteer has completed"""
        return self.volunteer_repository.get_past_volunteer_roles(volunteer_id)
    
    def signup_for_role(self, volunteer_id, event_id, role_id):
        """Sign up a volunteer for a specific role at an event"""
        # Check if there are still vacancies
        if not self.volunteer_repository.has_vacancy(event_id, role_id):
            return False, "This role is already full."
        
        # Check if volunteer is already signed up for this specific role
        if self.volunteer_repository.is_already_signed_up(volunteer_id, event_id, role_id):
            return False, "You are already signed up for this role."
        
        # Check if volunteer is already signed up for ANY role at this event
        if self.volunteer_repository.is_signed_up_for_event(volunteer_id, event_id):
            return False, "You are already signed up for a role at this event. Each volunteer can only have one role per event."
        
        # Check if volunteer is already signed up for another event on the same date
        if self.volunteer_repository.is_signed_up_for_same_date(volunteer_id, event_id):
            return False, "You are already signed up for another event on this date. Volunteers can only commit to one event per day."
        
        success = self.volunteer_repository.signup_for_role(volunteer_id, event_id, role_id)
        if success:
            return True, "Successfully signed up for volunteer role!"
        else:
            return False, "Unable to sign up for this role. Please try again."
    
    def cancel_role(self, volunteer_id, event_id, role_id):
        """Cancel a volunteer's sign-up for a specific role"""
        success = self.volunteer_repository.cancel_role(volunteer_id, event_id, role_id)
        if success:
            return True, "Successfully cancelled volunteer role."
        else:
            return False, "Unable to cancel this role. Please try again."
