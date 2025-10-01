from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from participant.repository import assign_volunteer_task, cancel_volunteer_role, withdraw_application
from flask_login import login_required, current_user  # Assuming Flask-Login is used for user authentication

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
