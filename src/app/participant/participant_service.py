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
