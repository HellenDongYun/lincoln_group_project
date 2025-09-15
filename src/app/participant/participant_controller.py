from flask import Blueprint, render_template, request, flash, redirect, url_for

from src.app.auth.route_guard import route_guard
from src.app.common.nav.encode import decode_id
from src.app.user.user import Role
from src.app.participant.participant_service import ParticipantService

participant_service = ParticipantService()
participant_blueprint = Blueprint('participant', __name__)


@participant_blueprint.route("<encoded_participant_id>", methods=["GET"])
@route_guard(Role.PARTICIPANT)
def dashboard(encoded_participant_id):
    participant_id = decode_id(encoded_participant_id)
    
    # Get upcoming events that the participant can register for
    upcoming_events = participant_service.get_upcoming_events(participant_id)
    
    # Get participant's registered events
    my_registrations = participant_service.get_my_registrations(participant_id)
    
    # Get participant's past race results
    my_results = participant_service.get_my_race_results(participant_id)
    
    return render_template("participant/participant_dashboard.html", 
                         upcoming_events=upcoming_events,
                         my_registrations=my_registrations,
                         my_results=my_results,
                         participant_id=encoded_participant_id)


@participant_blueprint.route("<encoded_participant_id>/register/<int:event_id>", methods=["POST"])
@route_guard(Role.PARTICIPANT)
def register_for_event(encoded_participant_id, event_id):
    participant_id = decode_id(encoded_participant_id)
    
    try:
        success = participant_service.register_for_event(participant_id, event_id)
        
        if success:
            flash("Successfully registered for the event!", "success")
        else:
            flash("Registration failed. Event may be full or you may already be registered.", "danger")
    except Exception as e:
        flash(f"Registration error: {str(e)}", "danger")
    
    return redirect(url_for('participant.dashboard', encoded_participant_id=encoded_participant_id))


@participant_blueprint.route("<encoded_participant_id>/cancel/<int:event_id>", methods=["POST"])
@route_guard(Role.PARTICIPANT)
def cancel_registration(encoded_participant_id, event_id):
    participant_id = decode_id(encoded_participant_id)
    
    try:
        success = participant_service.cancel_registration(participant_id, event_id)
        
        if success:
            flash("Successfully cancelled your registration for the event.", "success")
        else:
            flash("Cancellation failed. You may not be registered for this event.", "danger")
    except Exception as e:
        flash(f"Cancellation error: {str(e)}", "danger")
    
    return redirect(url_for('participant.dashboard', encoded_participant_id=encoded_participant_id))
