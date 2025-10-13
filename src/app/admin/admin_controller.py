import math
from flask import Blueprint, jsonify, render_template, request, flash, redirect, session, url_for
from src.app.admin.admin_service import AdminService
from src.app.common.date_format import DateFormat
from src.app.common.db.cursor import get_cursor
from src.app.app_controller import admin_service
from src.app.auth.route_guard import require_super_admin
from src.app.auth.auth_service import auth_service
from src.app.common.nav.encode import decode_id
from src.app.user.user import GlobalRole
from datetime import datetime

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import check_password_hash, generate_password_hash
# from werkzeug.utils import secure_filename
# from src.app import db 
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS



""" Example Repo-Service-Controller """ 
admin_blueprint = Blueprint('admin', __name__)
@admin_blueprint.route("<encoded_admin_id>", methods=["GET", "POST"])
@require_super_admin
def get_admin(encoded_admin_id):
    admin_id = decode_id(encoded_admin_id)
    admin = admin_service.get_admin_by_admin_id(admin_id)
    return render_template("admin/admin.html", admin=admin)

@admin_blueprint.route("/events/<int:event_id>/volunteer_roles", methods=["GET", "POST"])
# @route_guard(Role.ADMIN)
def manage_volunteer_roles(event_id):
    # get event name
    event_name = AdminService.get_event_name(event_id)
    #get volunteer role
    volunteer_roles = AdminService.fetch_all_volunteer_roles()
    assigned_roles = AdminService.get_assigned_roles(event_id)
    form_data = {}
    if request.method == "POST":
        if "remove_role" in request.form:
            role_id = request.form.get("role_id")
            AdminService.remove_volunteer_role(event_id, role_id)
            assigned_roles = AdminService.get_assigned_roles(event_id)
            return render_template("admin/manage_volunteer_roles.html",event_name=event_name, event_id=event_id,volunteer_roles=volunteer_roles,assigned_roles=assigned_roles,form_data={})
        else:
            role_id = request.form.get("role_id")
            spots = request.form.get("spots")
            form_data = {'role_id': role_id, 'spots': spots}
            errors, spots_int = validate_form(role_id, spots)
            if errors:
                for error in errors:
                    flash(error, "danger")
                return render_template("admin/manage_volunteer_roles.html",event_name=event_name,event_id=event_id,volunteer_roles=volunteer_roles,assigned_roles=assigned_roles,form_data=form_data)
            AdminService.upsert_volunteer_role(event_id, role_id, spots_int)
            
            # Get role name for flash message
            role_name = None
            for role in volunteer_roles:
                if str(role['id']) == str(role_id):
                    role_name = role['name']
                    break
            
            # Check if request came from dashboard
            from_dashboard = request.form.get("from_dashboard") == "true"
            
            if from_dashboard:
                flash(f"{spots_int} {role_name} {'spot' if spots_int == 1 else 'spots'} added for {event_name}!", "success")
                return redirect(url_for("admin.admin_dashboard"))
            else:
                flash("Volunteer role requirement updated!", "success")
                return redirect(url_for("admin.manage_volunteer_roles", event_id=event_id))
    # get method returns
    return render_template("admin/manage_volunteer_roles.html",event_name=event_name,event_id=event_id, volunteer_roles=volunteer_roles,assigned_roles=assigned_roles,form_data=form_data)


def validate_form(role_id, spots):
    errors = []
    spots_int = None
    if not role_id:
        errors.append("Please select a role before submitting!")
    if not spots:
        errors.append("Please enter number of spots!")
    else:
        try:
            spots_int = int(spots)
            if spots_int <= 0:
                errors.append("Number of spots must be a positive integer!")
            elif spots_int > 50:
                errors.append("Number of spots must be less than or equal to 50!")
        except ValueError:
            errors.append("Number of spots must be an integer!")
    return errors, spots_int

     
@admin_blueprint.route("/events",methods=['GET','POST'])  
# @route_guard(Role.ADMIN)
def view_events():
    # get parameters from request
    filters = {
        "name": request.args.get("name", "").strip(),
        "town": request.args.get("town", "").strip(),
        "order": request.args.get("order", "asc"),
        "page": int(request.args.get("page", 1)),
        "per_page": 10,
    }
    # call service get the events
    events, page, total_pages = AdminService.get_events(filters)
    return render_template(
        "admin/view_events.html",
        upcome_events=events,
        page=page,
        per_page=filters["per_page"],
        total_pages=total_pages,
        name=filters["name"],
        town=filters["town"],
        order=filters["order"],
        DateFormat=DateFormat,
    )        

@admin_blueprint.route("/events/create", methods=['GET', 'POST'])
# @route_guard(Role.ADMIN)
def create_event():
    """Route for creating new events"""
    if request.method == 'POST':
        # Handle form submission for creating event
        # TODO: Add event creation logic here
        flash("Event creation functionality coming soon!", "info")
        return redirect(url_for('admin.view_events'))
    
    # For GET requests, show the create event form
    return render_template("admin/create-event.html")

@admin_blueprint.route("/events/<int:event_id>")
# @route_guard(Role.ADMIN)
def view_event_details(event_id):
    details = AdminService.get_event_details(event_id)
    return render_template(
        "admin/view_event_detail.html",
        event=details["event"],
        volunteer_roles=details["volunteer_roles"],
        participants=details["participants"],
        event_register_user_count=details["event_register_user_count"],
        volunteer_total_amount=details["volunteer_total_amount"],
        DateFormat=DateFormat,
        datetime=datetime
    )
    
@admin_blueprint.route('events/<int:event_id>/delete', methods = ['POST'])
# @route_guard(Role.ADMIN)
def admin_delete_event(event_id):
    try:
        AdminService.delete_event(event_id)
        flash(f"Event {event_id} deleted successfully.", "success")
    except Exception as e:
        flash(f"Failed to delete event: {str(e)}", "danger")
    return redirect(url_for('admin.view_events'))

@admin_blueprint.route("/events/<int:event_id>/<int:user_id>/update_user_role", methods=["POST"])
def update_user_role(event_id, user_id):
    new_role = request.form.get("role")   # volunteer / admin
    selected_role_id = request.form.get("role_id")  # volunteer_role id
    if new_role == "volunteer" and not selected_role_id:
        flash("Please select a volunteer role.", "danger")
        return redirect(url_for("admin.view_event_details", event_id=event_id))
    with get_cursor() as cursor:
         # get current user's role
        cursor.execute(
            "SELECT role FROM users WHERE id = %s",
            (user_id,),
        )
        user= cursor.fetchone()
        old_role = user["role"] if user else None
        if new_role == "volunteer":
            cursor.execute(
            """
            UPDATE users
            SET role = %s
            WHERE id = %s
            """,
            ('volunteer',user_id),
        )
            cursor.execute(
            """
            DELETE FROM Event_Participants
            WHERE event_id = %s AND user_id = %s
            """,
            (event_id, user_id),
            )
            # update vacancies
            cursor.execute(
                "SELECT spots FROM vacancies WHERE event_id = %s AND role_id = %s",
                (event_id, selected_role_id)
            )
            vacancy = cursor.fetchone()
            MAX_SPOTS = 50
            if vacancy:
                if vacancy['spots'] < MAX_SPOTS:
                    cursor.execute(
                        "UPDATE Vacancies SET spots = spots + 1 WHERE event_id = %s AND role_id = %s",
                        (event_id, selected_role_id)
                    )
                else:
                    flash("Volunteer spots for this role are full. Please choose a different role.", "danger")
                    return redirect(url_for("admin.view_event_details", event_id=event_id))
            else:
                cursor.execute(
                    "INSERT INTO Vacancies (event_id, role_id, spots) VALUES (%s, %s, %s)",
                    (event_id, selected_role_id, 1)
                )
         # ========== admin ==========
        elif new_role == "admin":
            # change to admin 
            cursor.execute(
                """
                UPDATE users
                SET role = %s
                WHERE id = %s
                """,
                ('super_admin',user_id),
            )  
        flash("User role updated successfully.", "success")
        return redirect(url_for("admin.view_event_details", event_id=event_id))           


@admin_blueprint.route('/')
# @route_guard(Role.ADMIN)
def admin_dashboard():
    event_filters_form = {
        "type": request.args.get("event_type", "").strip(),
        "town": request.args.get("event_town", "").strip(),
        "timeframe": request.args.get("event_timeframe", "30").strip() or "30",
        "search": request.args.get("event_search", "").strip(),
    }
    event_filters_query = {
        "type": event_filters_form["type"] or None,
        "town": event_filters_form["town"] or None,
        "timeframe": event_filters_form["timeframe"] or "30",
        "search": event_filters_form["search"] or None,
    }

    group_filters_form = {
        "search": request.args.get("group_search", "").strip(),
        "visibility": request.args.get("group_visibility", "").strip(),
        "status": request.args.get("group_status", "").strip(),
        "town": request.args.get("group_town", "").strip(),
        "has_events": request.args.get("group_has_events", "").strip(),
    }
    group_filters_query = {
        "search": group_filters_form["search"] or None,
        "visibility": group_filters_form["visibility"] or None,
        "status": group_filters_form["status"] or None,
        "town": group_filters_form["town"] or None,
        "has_events": group_filters_form["has_events"] or None,
    }

    monitoring_timeframe = request.args.get("monitoring_timeframe", "30").strip() or "30"
    try:
        monitoring_days = max(1, int(monitoring_timeframe))
    except ValueError:
        monitoring_days = 30
        monitoring_timeframe = "30"

    upcoming_events = AdminService.get_upcoming_events_with_volunteers(event_filters_query)
    volunteer_roles = AdminService.fetch_all_volunteer_roles()
    groups_overview = AdminService.get_group_overview(group_filters_query)
    pending_applications = AdminService.get_pending_group_applications()
    group_filter_options = AdminService.get_group_filter_options()
    event_filter_options = AdminService.get_event_filter_options()
    monitoring_metrics = AdminService.get_monitoring_metrics(monitoring_days)

    return render_template(
        "admin/dashboard.html",
        upcoming_events=upcoming_events,
        volunteer_roles=volunteer_roles,
        groups_overview=groups_overview,
        pending_applications=pending_applications,
        group_filter_options=group_filter_options,
        event_filter_options=event_filter_options,
        monitoring_metrics=monitoring_metrics,
        event_filters=event_filters_form,
        group_filters=group_filters_form,
        monitoring_filters={"timeframe": monitoring_timeframe},
    )


@admin_blueprint.route('/groups/<int:group_id>/assign-manager', methods=['POST'])
@require_super_admin
def assign_group_manager(group_id):
    manager_email = request.form.get('manager_email', '').strip()

    try:
        result = AdminService.assign_group_manager(group_id, manager_email)
        flash(f"Assigned {result['full_name']} ({result['email']}) as group manager.", "success")
    except ValueError as exc:
        flash(str(exc), "danger")
    except Exception as exc:
        flash(f"Unable to assign manager: {str(exc)}", "danger")

    return redirect(url_for('admin.admin_dashboard') + '#groups-insights')


@admin_blueprint.route('/groups/create', methods=['POST'])
@require_super_admin
def create_group():
    name = request.form.get('group_name', '').strip()
    description = request.form.get('group_description', '').strip()
    town = request.form.get('group_town', '').strip()
    visibility = request.form.get('group_visibility', 'public').strip() or 'public'
    manager_email = request.form.get('group_manager_email', '').strip()

    created_by = auth_service.get_user_id()

    try:
        result = AdminService.create_group(
            name=name,
            description=description,
            town=town,
            visibility=visibility,
            created_by=created_by,
            manager_email=manager_email
        )

        flash(f"Community group '{name}' created successfully.", "success")
        manager_result = result.get('manager')
        if manager_result:
            flash(
                f"Assigned {manager_result['full_name']} ({manager_result['email']}) as group manager.",
                "success",
            )
        elif result.get('manager_warning'):
            flash(result['manager_warning'], "warning")

    except ValueError as exc:
        flash(str(exc), "danger")
    except Exception as exc:
        flash(f"Unable to create group: {str(exc)}", "danger")

    return redirect(url_for('admin.admin_dashboard') + '#groups-insights')

@admin_blueprint.route("/remove_volunteer_role_dashboard", methods=["POST"])
# @route_guard(Role.ADMIN)
def remove_volunteer_role_dashboard():
    """Remove volunteer role from event via dashboard"""
    event_id = request.form.get("event_id")
    role_name = request.form.get("role_name")
    
    if not event_id or not role_name:
        flash("Error: Missing event ID or role name.", "danger")
        return redirect(url_for("admin.admin_dashboard"))
    
    try:
        # Get role ID from role name
        volunteer_roles = AdminService.fetch_all_volunteer_roles()
        role_id = None
        for role in volunteer_roles:
            if role['name'] == role_name:
                role_id = role['id']
                break
        
        if not role_id:
            flash("Error: Volunteer role not found.", "danger")
            return redirect(url_for("admin.admin_dashboard"))
        
        # Remove the volunteer role
        AdminService.remove_volunteer_role(event_id, role_id)
        
        # Get event name for flash message
        event_name = AdminService.get_event_name(event_id)
        flash(f"Volunteer role '{role_name}' removed from {event_name}.", "success")
        
    except Exception as e:
        flash(f"Error removing volunteer role: {str(e)}", "danger")
    
    return redirect(url_for("admin.admin_dashboard"))

@admin_blueprint.route("/volunteers")
# @route_guard(Role.ADMIN)
def view_all_volunteers():
    page = int(request.args.get("page", 1))
    per_page = 10
    filters = {
        "role_name": request.args.get("role_name"),
        "event_name": request.args.get("event_name"),
        "location": request.args.get("location")
    }
    data = AdminService.get_all_volunteer_roles(filters, page, per_page)
    volunteer_required = 50
    return render_template("admin/view_all_volunteers.html",volunteers=data["volunteers"],DateFormat=DateFormat,volunteer_required=volunteer_required,page=data["page"],
        per_page=data["per_page"],
        total_pages=data["total_pages"],
        filters=data["filters"])

@admin_blueprint.route("/volunteers/delete_volunteer_role/<int:event_id>/<int:role_id>", methods=["POST"])
# @route_guard(Role.ADMIN)
def delete_volunteer_role(event_id,role_id):
    try:
        with get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM Event_Task_Vacancies WHERE event_id = %s AND task_id = %s",
                (event_id, role_id)
            )
        flash(f"Volunteer role with ID {role_id} has been deleted.", "success")
    except Exception as e:
        flash(f"Error deleting volunteer role: {str(e)}", "danger")
    return redirect(url_for("admin.view_all_volunteers"))

@admin_blueprint.route("/set_user_status/<int:user_id>/<int:event_id>/<status>", methods=["POST"])
# @route_guard(Role.ADMIN)
def set_user_status(user_id,event_id, status):
    try:
        updated_status = AdminService.set_user_status(user_id, event_id, status)
        flash(f"User with ID {user_id} status updated to {updated_status}", "success")
    except ValueError as e:
        flash(str(e), "danger")
    
    # Check if the request came from the event details page or manage participants page
    referrer = request.referrer
    if referrer and 'events' in referrer and str(event_id) in referrer:
        return redirect(url_for("admin.view_event_details", event_id=event_id))
    elif referrer and 'manage-event-participants' in referrer:
        return redirect(url_for("admin.manage_event_participant"))
    else:
        return redirect(url_for("admin.manage_event_participant"))

@admin_blueprint.route("/manage-event-participants")
# @route_guard(Role.ADMIN)
def manage_event_participant():
    full_name = request.args.get("full_name", "").strip()
    role = request.args.get("role", "").strip()
    status = request.args.get("status", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 10
    if request.args and (full_name == "" and role == "" and status == ""):
        flash("Please enter at least one search condition for filtering", "warning")
    
    all_users = AdminService.get_event_participants(full_name=full_name,
    role=role,
    status=status,
    page=page,
    per_page=per_page)
    
    total_users = AdminService.count_event_participants(
    full_name=full_name,
    role=role,
    status=status
    )
    if (full_name or role or status) and not all_users:
        flash("No participants who meet the requirements were found. Please try other filters", "info")
    total_pages = math.ceil(total_users / per_page)
    
    return render_template("admin/manage_event_participant.html",all_users=all_users,DateFormat=DateFormat,full_name=full_name,role=role,status=status,page=page,total_pages=total_pages,per_page=per_page )

@admin_blueprint.route('/results')  
# @route_guard(Role.ADMIN)
def view_event_results():
    with get_cursor() as cursor:
        results = AdminService.get_results()
        return render_template("admin/view_event_results.html",results=results,DateFormat=DateFormat)  
    


@admin_blueprint.route('/users/roles')
# @route_guard(Role.ADMIN)
def manage_user_roles():
    """Page for managing user roles"""
    page = int(request.args.get('page', 1))
    per_page = 15
    search_name = request.args.get('search_name', '').strip()
    search_role = request.args.get('search_role', '').strip()
    
    # Convert empty strings to None
    search_name = search_name if search_name else None
    search_role = search_role if search_role else None
    
    user_data = AdminService.get_users_for_role_management(
        page=page, 
        per_page=per_page, 
        search_name=search_name, 
        search_role=search_role
    )
    
    return render_template('admin/manage_user_roles.html', 
                         users=user_data['users'],
                         page=user_data['page'],
                         per_page=user_data['per_page'],
                         total_pages=user_data['total_pages'],
                         total_count=user_data['total_count'],
                         search_name=search_name or '',
                         search_role=search_role or '')

@admin_blueprint.route('/users/<int:user_id>/role', methods=['POST'])
# @route_guard(Role.ADMIN)
@require_super_admin
def update_user_role_ajax(user_id):
    """Update user role via AJAX"""
    try:
        new_role = request.form.get('new_role')

        # Validate role
        valid_roles = ['participant', 'group_manager', 'support_technician', 'super_admin']
        if new_role not in valid_roles:
            return {'success': False, 'message': 'Invalid role specified'}, 400
        
        # Get user details first
        user = AdminService.get_user_by_id(user_id)
        if not user:
            return {'success': False, 'message': 'User not found'}, 404
        
        # Update the role
        success = AdminService.update_user_role(user_id, new_role)
        
        if success:
            flash(f"Successfully updated {user['full_name']}'s role to {new_role.title()}", "success")
            return {'success': True, 'message': f"Role updated to {new_role.title()}"}, 200
        else:
            return {'success': False, 'message': 'Failed to update role'}, 500
            
    except Exception as e:
        return {'success': False, 'message': f'Error: {str(e)}'}, 500

@admin_blueprint.route('/users/<int:user_id>/status', methods=['POST'])
# @route_guard(Role.ADMIN)
@require_super_admin
def update_user_status_ajax(user_id):
    """Update user status via AJAX"""
    try:
        new_status = request.form.get('new_status')
        
        # Validate status
        valid_statuses = ['active', 'inactive']
        if new_status not in valid_statuses:
            return {'success': False, 'message': 'Invalid status specified'}, 400
        
        # Get user details first
        user = AdminService.get_user_by_id(user_id)
        if not user:
            return {'success': False, 'message': 'User not found'}, 404
        
        # Update the status
        success = AdminService.update_user_status(user_id, new_status)
        
        if success:
            status_action = "activated" if new_status == "active" else "deactivated"
            flash(f"Successfully {status_action} {user['full_name']}", "success")
            return {'success': True, 'message': f"User {status_action}"}, 200
        else:
            return {'success': False, 'message': 'Failed to update status'}, 500
            
    except Exception as e:
        return {'success': False, 'message': f'Error: {str(e)}'}, 500






    
    
    
    
    