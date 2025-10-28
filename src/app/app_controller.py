from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_bcrypt import generate_password_hash, check_password_hash

from src.app.admin.admin_service import AdminService
from src.app.auth.auth_service import AuthService
from src.app.common.file_service import FileService
from src.app.common.form_group import FormGroup, FormControl
from src.app.event.event_service import EventService
from src.app.town.town_service import TownService
from src.app.user.user import GlobalRole
from src.app.user.user_service import UserService
from src.app.home_service import HomeService
from src.app.group.group_service import GroupService
from src.app.participant.participant_service import ParticipantService

admin_service = AdminService()
auth_service = AuthService()
event_service = EventService()
file_service = FileService()
town_service = TownService()
user_service = UserService()
home_service = HomeService()
participant_service = ParticipantService()

app_blueprint = Blueprint('app', __name__)

# map UI age_group string to a representative age integer.
# Returns None when age_group is unspecified ("Prefer not to say").
def map_age_group_to_age(age_group: str | None) -> int | None:
    if not age_group:
        return None
    if age_group == 'Under 18':
        return 16
    if age_group == '18-29':
        return 25
    if age_group == '30-44':
        return 37
    if age_group == '45+':
        return 50
    return None

@app_blueprint.route("")
def home():
    # Get next 5 upcoming events for home page
    upcoming_events = home_service.get_upcoming_events(5)
    location_options = home_service.get_event_locations()
    return render_template(
        "app/home.html",
        is_logged_in=auth_service.is_logged_in(),
        upcoming_events=upcoming_events,
        location_options=location_options,
        selected_location="",
        selected_event_type="all",
        selected_date_filter="next_2_weeks",
    )

@app_blueprint.route("login", methods=["GET", "POST"])
def login():

    form_group = FormGroup({
        "email": FormControl(''),
        "password": FormControl('')
    })

    
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        
        # Store values in form group for re-display
        form_group.get("email").value = email
        form_group.get("password").value = password

        user, error_message = user_service.validate_user(email, password)

        if user:
            auth_service.login(user.id, user.global_role)
            flash("Login successful.", "success")

            # Redirect based on role
            if auth_service.is_super_admin():
                return redirect(url_for("admin.admin_dashboard", encoded_admin_id=user.encoded_user_id))
            elif auth_service.is_support_technician():
                return redirect(url_for("support.support_queue"))
            elif auth_service.is_participant():
                managed_groups = GroupService.get_user_managed_groups(user.id)
                if managed_groups:
                    first_group_id = managed_groups[0]['id']
                    return redirect(url_for('groups.manager_dashboard', group_id=first_group_id))
                return redirect(url_for("participant.dashboard", encoded_participant_id=user.encoded_user_id))
            else:
                flash("Unknown role. Contact support.", "danger")
                return redirect(url_for("app.login"))
        else:
            if error_message == "Invalid email.":
                form_group.get("email").errors.append(error_message)
            elif error_message == "Please contact super.admin@platform.org to reset password.":
                form_group.get("password").errors.append(error_message)
                form_group.get("password").value = ''
            else:
                form_group.get("password").errors.append(error_message or "Invalid email or password.")


    return render_template("app/login.html", form_group=form_group)


@app_blueprint.route("logout")
def logout():

    auth_service.logout()
    flash("You have been logged out.", "info")
    return redirect(url_for("app.home"))

@app_blueprint.route("register", methods=["GET", "POST"])
def register():
    form_group = FormGroup({
        "first_name": FormControl(''),
        "last_name": FormControl(''),
        "town": FormControl(''),
        "gender": FormControl(''),
        "age_group": FormControl(''),
        "email": FormControl(''),
        "password": FormControl(''),
        "password_confirmation": FormControl(''),
    })

    if request.method == "POST":
        first_name_input = request.form.get('first_name', '').strip()
        last_name_input = request.form.get('last_name', '').strip()
        town_input = request.form.get('town', '').strip()
        email_input = request.form.get('email', '').strip()
        gender_input = request.form.get('gender', '').strip() or None
        age_group_input = request.form.get('age_group', '').strip() or None
        password_input = request.form.get('password', '').strip()
        password_confirmation_input = request.form.get('password_confirmation', '').strip()

        form_group.get("first_name").value = first_name_input
        form_group.get("last_name").value = last_name_input
        form_group.get("town").value = town_input
        form_group.get("gender").value = gender_input or ''
        form_group.get("age_group").value = age_group_input or ''
        form_group.get("email").value = email_input
        form_group.get("password").value = password_input
        form_group.get("password_confirmation").value = password_confirmation_input

        # Validate input
        errors = user_service.validate_name_input(first_name_input, "First name")
        if errors:
            form_group.get("first_name").errors.extend(errors)

        errors = user_service.validate_name_input(last_name_input, "Last name")
        if errors:
            form_group.get("last_name").errors.extend(errors)

        errors = user_service.validate_name_input(town_input, "Town")
        if errors:
            form_group.get("town").errors.extend(errors)

        errors, normalised_email = user_service.validate_email_input(email_input)
        if errors:
            form_group.get("email").errors.extend(errors)

        errors = user_service.validate_password_input(password_input)
        if errors:
            form_group.get("password").errors.extend(errors)

        if password_confirmation_input != password_input:
            form_group.get("password_confirmation").errors.append("Password confirmation must match password.")

        if not form_group.is_valid():
            return render_template("app/register.html", form_group=form_group)

        # Create User
        password_hash = generate_password_hash(password_input)
        # Map age_group to representative age integer
        age_value = map_age_group_to_age(age_group_input)

        success = user_service.create_user(
            (first_name_input, last_name_input, town_input, normalised_email, password_hash, 'participant', gender_input, age_value)
        )

        if not success:
            flash("Registration failed.", "danger")
            return render_template("app/register.html", form_group=form_group)

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("app.login"))

    return render_template("app/register.html", form_group=form_group)


@app_blueprint.route("settings", methods=["GET", "POST"])
def settings():
    # Check if user is logged in
    if not auth_service.is_logged_in():
        flash("Please log in to access settings.", "warning")
        return redirect(url_for("app.login"))
    
    user_id = auth_service.get_user_id()
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("app.home"))
    
    form_group = FormGroup({
        "first_name": FormControl(user.get('first_name', '')),
        "last_name": FormControl(user.get('last_name', '')),
        "town": FormControl(user.get('town', '')),
        "gender": FormControl(user.get('gender', '') or ''),
        "age_group": FormControl(user.get('age_group', '') or ''),
        "current_password": FormControl(''),
        "new_password": FormControl(''),
        "confirm_password": FormControl('')
    })
    
    if request.method == "POST":
        first_name_input = request.form.get('first_name', '').strip()
        last_name_input = request.form.get('last_name', '').strip()
        town_input = request.form.get('town', '').strip()
        gender_input = request.form.get('gender', '').strip() or None
        age_group_input = request.form.get('age_group', '').strip() or None
        current_password_input = request.form.get('current_password', '').strip()
        new_password_input = request.form.get('new_password', '').strip()
        confirm_password_input = request.form.get('confirm_password', '').strip()
        
        form_group.get("first_name").value = first_name_input
        form_group.get("last_name").value = last_name_input
        form_group.get("town").value = town_input
        form_group.get("gender").value = gender_input or ''
        form_group.get("age_group").value = age_group_input or ''
        form_group.get("current_password").value = current_password_input
        form_group.get("new_password").value = new_password_input
        form_group.get("confirm_password").value = confirm_password_input
        
        # Validate basic fields
        errors = user_service.validate_name_input(first_name_input, "First name")
        if errors:
            form_group.get("first_name").errors.extend(errors)
            
        errors = user_service.validate_name_input(last_name_input, "Last name")
        if errors:
            form_group.get("last_name").errors.extend(errors)
            
        errors = user_service.validate_name_input(town_input, "Town")
        if errors:
            form_group.get("town").errors.extend(errors)
            
        # Password change validation (only if new password is provided)
        if new_password_input:
            if not current_password_input:
                form_group.get("current_password").errors.append("Current password is required to change password.")
            else:
                # Verify current password
                if not check_password_hash(user.get('password_hash'), current_password_input):
                    form_group.get("current_password").errors.append("Current password is incorrect.")
                else:
                    # Check if new password is the same as current password
                    if check_password_hash(user.get('password_hash'), new_password_input):
                        form_group.get("new_password").errors.append("New password must be different from your current password.")
            
            errors = user_service.validate_password_input(new_password_input)
            if errors:
                form_group.get("new_password").errors.extend(errors)
                
            if confirm_password_input != new_password_input:
                form_group.get("confirm_password").errors.append("Password confirmation must match new password.")
        
        if not form_group.is_valid():
            return render_template("app/settings.html", form_group=form_group)
        
        # Update user information
        update_data = {
            'first_name': first_name_input,
            'last_name': last_name_input,
            'town': town_input
        }

        # Map age_group to representative age (or clear if unspecified)
        update_data['age'] = map_age_group_to_age(age_group_input)

        # Update gender if provided
        if gender_input in ['male', 'female', 'other', None]:
            update_data['gender'] = gender_input
        
        # Add password hash if password is being changed
        if new_password_input:
            update_data['password_hash'] = generate_password_hash(new_password_input)
        
        success = user_service.update_user(user_id, update_data)
        
        if success:
            flash("Settings updated successfully.", "success")
            return redirect(url_for("app.settings"))
        else:
            flash("Failed to update settings.", "danger")
    
    return render_template("app/settings.html", form_group=form_group)

# home page as visitor when filter events
@app_blueprint.route("/search")
def home_filter_events():
    filter_type = request.args.get("filter_type", "events")  
    location = request.args.get("location", "").strip()
    event_type = request.args.get("event_type", "").strip()
    date_param = request.args.get("date", "").strip()
    formatted_date = ""
    allowed_ranges = {"next_2_weeks", "next_3_months", "all"}
    limit = 9
    if filter_type == "events" and not date_param:
        date_param = "next_2_weeks"
    if date_param and date_param not in allowed_ranges:
        try:
            date_obj = datetime.strptime(date_param, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d/%m/%Y")
        except ValueError:
            formatted_date = date_param
    filter_event_results = []
    filter_group_results = []
    if filter_type == "events":
        filter_event_results = HomeService.home_filter_events(limit, location, event_type, date_param)
        if auth_service.is_logged_in() and auth_service.is_participant():
            user_id = auth_service.get_user_id()

            registered_event_ids = set()
            try:
                my_registrations = participant_service.get_my_registrations(user_id) or []
                registered_event_ids = {
                    record.get('Event_ID') for record in my_registrations if record.get('Event_ID') is not None
                }
            except Exception:
                registered_event_ids = set()

            member_group_ids = set()
            try:
                user_groups = GroupService.get_user_groups(user_id) or []
                member_group_ids = {
                    group.get('id')
                    for group in user_groups
                    if group.get('id') is not None and (group.get('member_status') or 'active') == 'active'
                }
            except Exception:
                member_group_ids = set()

            for event in filter_event_results or []:
                event_id = event.get('id')
                group_id = event.get('group_id')
                visibility = (event.get('visibility') or '').strip().lower()
                is_registered = event_id in registered_event_ids
                is_group_member = group_id in member_group_ids if group_id is not None else False

                if visibility == 'private' and not is_group_member:
                    event['disable_quick_register'] = True
                    event['quick_register_label'] = "Apply to Join"
                else:
                    event['disable_quick_register'] = bool(is_registered)
                    event['quick_register_label'] = "Registered" if is_registered else "Register Now"
    elif filter_type == "groups":
        filter_group_results = HomeService.home_filter_groups()
        for group in filter_group_results or []:
            group_id = group.get('group_id') or group.get('id')
            group['group_id'] = group_id
            upcoming_events = []
            has_more_events = False

            if group_id is not None:
                try:
                    raw_events = GroupService.get_group_events(group_id, include_past=False, limit=4)
                    has_more_events = len(raw_events) > 3
                    for event in raw_events[:3]:
                        if not event:
                            continue

                        datetime_label = getattr(event, 'datetime_str', None)
                        if not datetime_label and getattr(event, 'datetime', None):
                            try:
                                datetime_label = event.datetime.strftime('%d %b %Y %H:%M')
                            except Exception:
                                datetime_label = None

                        upcoming_events.append({
                            'id': event.id,
                            'name': event.name,
                            'datetime_label': datetime_label or 'Date to be confirmed',
                            'town': event.town,
                            'event_type': event.event_type,
                        })
                except Exception:
                    upcoming_events = []
                    has_more_events = False

            group['upcoming_events'] = upcoming_events
            group['has_more_events'] = has_more_events

        if auth_service.is_logged_in() and auth_service.is_participant():
            user_id = auth_service.get_user_id()

            active_group_ids = set()
            try:
                user_groups = GroupService.get_user_groups(user_id) or []
                active_group_ids = {
                    group.get('id')
                    for group in user_groups
                    if group.get('id') is not None and (group.get('member_status') or 'active') == 'active'
                }
            except Exception:
                active_group_ids = set()

            pending_group_ids = set()
            try:
                pending_requests = GroupService.get_user_pending_requests(user_id) or []
                pending_group_ids = {
                    request.get('group_id')
                    for request in pending_requests
                    if request.get('group_id') is not None
                }
            except Exception:
                pending_group_ids = set()

            for group in filter_group_results or []:
                group_id = group.get('group_id') or group.get('id')
                visibility = (group.get('visibility') or '').lower()
                is_member = group_id in active_group_ids
                has_pending = group_id in pending_group_ids

                disable_join = bool(is_member or has_pending)
                if is_member:
                    label = "Member"
                    icon = "bi-check-circle"
                elif has_pending:
                    label = "Pending"
                    icon = "bi-hourglass-split"
                elif visibility == 'public':
                    label = "Join group"
                    icon = "bi-person-plus-fill"
                else:
                    label = "Apply to Join"
                    icon = "bi-envelope-plus"

                group['disable_join'] = disable_join
                group['join_label'] = label
                group['join_icon'] = icon
                group['join_action'] = 'join' if visibility == 'public' else 'request'
    location_options = home_service.get_event_locations()
    selected_date_filter = date_param if date_param in allowed_ranges else ("all" if date_param else "next_2_weeks")
    return render_template(
        "app/search.html",
        events=filter_event_results,
        groups=filter_group_results,
        filter_type=filter_type,
        location=location,
        event_type=event_type,
        date_str=formatted_date,
        selected_location=location,
        selected_event_type=event_type or "all",
        selected_date_filter=selected_date_filter,
        location_options=location_options,
        is_logged_in=auth_service.is_logged_in(),
        is_participant=auth_service.is_participant(),
        current_user_id=auth_service.get_user_id(),
    )


@app_blueprint.route("/events/<int:event_id>/quick-register", methods=["POST"])
def quick_register_event(event_id: int):
    """Allow logged-in visitors to join an open group and register for an event from the discovery page."""
    fallback_url = url_for("app.home_filter_events", filter_type="events")
    requested_next = (request.form.get("next") or "").strip()
    redirect_target = fallback_url
    if requested_next and requested_next.startswith("/"):
        redirect_target = requested_next

    if not auth_service.is_logged_in():
        flash("Please log in to register for events.", "warning")
        return redirect(url_for("app.login"))

    if not auth_service.is_participant():
        flash("Only participant accounts can register for events.", "warning")
        return redirect(redirect_target)

    user_id = auth_service.get_user_id()
    event = event_service.get_event_by_id(event_id)

    if not event:
        flash("Event not found.", "danger")
        return redirect(redirect_target)

    # Ensure the user belongs to the hosting group when it is public/open.
    if event.group_id:
        membership = GroupService.get_group_membership(event.group_id, user_id)
        if not membership:
            group = GroupService.get_group_by_id(event.group_id)
            visibility = (group or {}).get("visibility", "").strip().lower() if group else ""
            if visibility == "public":
                try:
                    GroupService.add_member_to_group(event.group_id, user_id)
                except Exception:
                    flash("Unable to join the hosting group at this time. Please try again later.", "danger")
                    return redirect(redirect_target)
            else:
                flash("You need to be a member of this group before registering for the event.", "warning")
                return redirect(url_for("groups.view_group", group_id=event.group_id))

    success = participant_service.register_for_event(user_id, event_id)
    if success:
        flash("You are registered for the event.", "success")
    else:
        flash("Unable to register for this event. It may be full or you may already be registered.", "danger")

    return redirect(redirect_target)

