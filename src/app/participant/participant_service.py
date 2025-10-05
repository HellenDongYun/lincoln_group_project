from src.app.participant.participant_repository import ParticipantRepository


class ParticipantService:
    def __init__(self):
        self.participant_repository = ParticipantRepository()
    
    def get_upcoming_events(self, participant_id):
        """Get all upcoming events that the participant is not already registered for"""
        return self.participant_repository.get_upcoming_events(participant_id)
    
    def get_my_registrations(self, participant_id):
        """Get events that the participant is registered for"""
        return self.participant_repository.get_my_registrations(participant_id)
    
    def get_my_race_results(self, participant_id):
        """Get participant's past race results"""
        return self.participant_repository.get_my_race_results(participant_id)
    
    def register_for_event(self, participant_id, event_id):
        """Register participant for an event"""
        return self.participant_repository.register_for_event(participant_id, event_id)
    
    def cancel_registration(self, participant_id, event_id):
        """Cancel participant registration for an event"""
        return self.participant_repository.cancel_registration(participant_id, event_id)


    def get_participant_applications(self,status="all", page=1,per_page=5,participant_id=None):
        """Get participant applications details"""
        return self.participant_repository.show_application(status=status, page= page,per_page=per_page,participant_id=participant_id)
    
    
    def submit_create_group_application(self,participant_id, name, town, visibility, description):
        """Get participant applications details"""
        if not name or not town or not visibility:
            raise ValueError("Group name, location, and visibility are required.")

        if visibility not in ["public", "private"]:
            raise ValueError("Invalid visibility option.")

        return self.participant_repository.create_group_application(participant_id, name, description, town, visibility)
    
    def get_application_by_id(self,participant_id, application_id):
        return self.participant_repository.get_application_by_id(participant_id, application_id)
    
    def update_group_application(self,participant_id, application_id, name, town, visibility, description):
        return self.participant_repository.update_group_application(participant_id, application_id, name, town, visibility, description)
    
    
    def delete_group_application(self,participant_id, application_id):
        return self.participant_repository.delete_group_application(participant_id, application_id, )
        