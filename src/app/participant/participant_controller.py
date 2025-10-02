
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from src.app.participant.repository import assign_volunteer_task, cancel_volunteer_role, withdraw_application
from flask_login import login_required, current_user  # Assuming Flask-Login is used for user authentication

from datetime import datetime
import math
from flask import Blueprint, render_template, request, flash, redirect, url_for


participant_bp = Blueprint('participant', __name__)

@participant_bp.route('/participant/sign_task', methods=['POST'])
@login_required
def sign_task():
    """
    Handle volunteer task registration requests. 
    After submission, the status will be pending approval.
    """
    data = request.get_json()
    event_name = data.get('event')
    role_name = data.get('role')
    volunteer_id = current_user.id if current_user.is_authenticated else None  # Get ID from the current user

    if not volunteer_id or not event_name or not role_name:
        return jsonify({'error': 'Missing required fields'}), 400


    # Call repository layer to handle task registration
    try:
        success = assign_volunteer_task(volunteer_id, event_name, role_name)
        if success:
            return jsonify({'message': 'Application submitted, pending approval'}), 200
        return jsonify({'error': 'Failed to submit application'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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


@participant_bp.route('/participant/cancel_role', methods=['POST'])
@login_required
def cancel_role():
    """
    Cancel an approved volunteer role.
    """
    data = request.get_json()
    event_name = data.get('event')
    volunteer_id = current_user.id if current_user.is_authenticated else None

    if not volunteer_id or not event_name:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        success = cancel_volunteer_role(volunteer_id, event_name)
        if success:
            return jsonify({'message': f'Successfully cancelled role for {event_name}'}), 200
        return jsonify({'error': 'Failed to cancel role'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@participant_bp.route('/participant/withdraw_application', methods=['POST'])
@login_required
def withdraw_application():
    """
    Withdraw a pending application.
    """
    data = request.get_json()
    event_name = data.get('event')
    volunteer_id = current_user.id if current_user.is_authenticated else None

    if not volunteer_id or not event_name:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        success = withdraw_application(volunteer_id, event_name)
        if success:
            return jsonify({'message': f'Successfully withdrawn application for {event_name}'}), 200
        return jsonify({'error': 'Failed to withdraw application'}), 500
    except Exception as e:

        return jsonify({'error': str(e)}), 500

# Route to render sign_task.html (optional, used for initial page load)
@participant_bp.route('/participant/sign_task', methods=['GET'])
@login_required
def show_sign_task():
    return render_template('app/participant/sign_task.html')

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

