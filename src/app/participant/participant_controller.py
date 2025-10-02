from datetime import datetime
import math
from flask import Blueprint, render_template, request, flash, redirect, url_for

from src.app.auth.route_guard import require_login
from src.app.common.nav.encode import decode_id
from src.app.user.user import GlobalRole
from src.app.participant.participant_service import ParticipantService

participant_service = ParticipantService()
participant_blueprint = Blueprint('participant', __name__)


@participant_blueprint.route("<encoded_participant_id>", methods=["GET"])
@require_login
def dashboard(encoded_participant_id):
    participant_id = decode_id(encoded_participant_id)
    
    # Get upcoming events that the participant can register for
    upcoming_events = participant_service.get_upcoming_events(participant_id)
    
    # Get participant's registered events
    my_registrations = participant_service.get_my_registrations(participant_id)
    
    # Get participant's past race results
    my_results = participant_service.get_my_race_results(participant_id)
    
    # Get participant's group applications
    # my_applications = participant_service.get_my_applications(participant_id)
    
    return render_template("participant/participant_dashboard.html", 
                         upcoming_events=upcoming_events,
                         my_registrations=my_registrations,
                         my_results=my_results,
                         participant_id=encoded_participant_id)


@participant_blueprint.route("<encoded_participant_id>/register/<int:event_id>", methods=["POST"])
@require_login
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
@require_login
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


@participant_blueprint.route("/<encoded_participant_id>/applications", methods=["GET"])
def myapplications(encoded_participant_id):
    participant_id = decode_id(encoded_participant_id)
    #  get filter parameters
    status = request.args.get("status", "all")
    page = int(request.args.get("page", 1))  # current page, default is 1
    per_page = 5  # every page show 5 data
    applications,total = participant_service.get_participant_applications(status=status, page= page,per_page=per_page,participant_id=participant_id)
    total_pages = math.ceil(total / per_page)
    return render_template("participant/applications.html", encoded_participant_id=encoded_participant_id, applications=applications, total_pages = total_pages, page=page, per_page=per_page,status=status)

@participant_blueprint.route("/<encoded_participant_id>/applications/apply", methods=["GET","POST"])
def create_group_applyform(encoded_participant_id):
    participant_id = decode_id(encoded_participant_id)
    application_id = request.args.get("app_id") 
    is_edit_mode = bool(application_id)
    application = None
    if is_edit_mode:
        application = participant_service.get_application_by_id(participant_id, application_id)
    if request.method == 'POST':
        name = request.form.get("groupName")
        town = request.form.get("location")
        visibility = request.form.get("privacy")
        description = request.form.get("description")
        # temporary application data to retain the input
        application = {
            "proposed_name": name,
            "proposed_town": town,
            "visibility": visibility,
            "proposed_description": description
        }
         # added New field verification logic
        if not name or not town or not visibility:
            flash("Please fill in all required fields: group name, location, and visibility.", "danger")
            return render_template("participant/create_group_form.html",
                                   encoded_participant_id=encoded_participant_id,
                                   application=application,is_edit_mode =is_edit_mode )
        try:
            if is_edit_mode:  # update
                participant_service.update_group_application(
                    participant_id, application_id, name, town, visibility, description
                )
                flash("Your group application has been updated successfully!", "success")
            else:  # add
                participant_service.submit_create_group_application(
                    participant_id, name, town, visibility, description
                )
                flash("Your group application has been submitted successfully!", "success")

            return redirect(url_for("participant.myapplications", encoded_participant_id=encoded_participant_id,is_edit_mode =is_edit_mode ))
        except ValueError as e:
            flash(str(e), "danger")
    print(f'controller: {application}')        
    return render_template("participant/create_group_form.html", encoded_participant_id=encoded_participant_id,application=application,is_edit_mode =is_edit_mode )

@participant_blueprint.route("/<encoded_participant_id>/applications/<application_id>/delete", methods=["POST"])
def delete_group_application(encoded_participant_id, application_id):
    participant_id = decode_id(encoded_participant_id)
    try:
        participant_service.delete_group_application(participant_id, application_id)
        flash("Group application deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting group application: {str(e)}", "danger")
    return redirect(url_for("participant.myapplications", encoded_participant_id=encoded_participant_id))