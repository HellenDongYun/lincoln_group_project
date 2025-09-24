from flask import Blueprint, render_template, request, flash, redirect, url_for

from src.app.auth.route_guard import require_login
from src.app.common.nav.encode import decode_id
from src.app.user.user import GlobalRole
from src.app.volunteer.volunteer_service import VolunteerService

volunteer_service = VolunteerService()
volunteer_blueprint = Blueprint('volunteer', __name__)


@volunteer_blueprint.route("<encoded_volunteer_id>", methods=["GET"])
@require_login
def dashboard(encoded_volunteer_id):
    volunteer_id = decode_id(encoded_volunteer_id)
    
    # Get available volunteer opportunities
    available_opportunities = volunteer_service.get_available_opportunities(volunteer_id)
    
    # Get volunteer's current upcoming sign-ups
    my_volunteer_roles = volunteer_service.get_volunteer_roles(volunteer_id)
    
    # Get volunteer's past completed roles
    past_volunteer_roles = volunteer_service.get_past_volunteer_roles(volunteer_id)
    
    return render_template("volunteer/volunteer.dashboard.html", 
                         available_opportunities=available_opportunities,
                         my_volunteer_roles=my_volunteer_roles,
                         past_volunteer_roles=past_volunteer_roles,
                         volunteer_id=encoded_volunteer_id)


@volunteer_blueprint.route("signup/<int:event_id>/<int:role_id>", methods=["POST"])
@require_login
def signup_for_role(event_id, role_id):
    # Get volunteer ID from the URL parameter
    encoded_volunteer_id = request.form.get('volunteer_id')
    volunteer_id = decode_id(encoded_volunteer_id)
    
    success, message = volunteer_service.signup_for_role(volunteer_id, event_id, role_id)
    
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    
    return redirect(url_for("volunteer.dashboard", encoded_volunteer_id=encoded_volunteer_id))


@volunteer_blueprint.route("cancel/<int:event_id>/<int:role_id>", methods=["POST"])
@require_login
def cancel_role(event_id, role_id):
    # Get volunteer ID from the URL parameter
    encoded_volunteer_id = request.form.get('volunteer_id')
    volunteer_id = decode_id(encoded_volunteer_id)
    
    success, message = volunteer_service.cancel_role(volunteer_id, event_id, role_id)
    
    if success:
        flash(message, "info")
    else:
        flash(message, "danger")
    
    return redirect(url_for("volunteer.dashboard", encoded_volunteer_id=encoded_volunteer_id))

