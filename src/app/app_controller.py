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

admin_service = AdminService()
auth_service = AuthService()
event_service = EventService()
file_service = FileService()
town_service = TownService()
user_service = UserService()
home_service = HomeService()

app_blueprint = Blueprint('app', __name__)

@app_blueprint.route("")
def home():
    # Get next 5 upcoming events for home page
    upcoming_events = home_service.get_upcoming_events(5)
    return render_template("app/home.html", 
                         is_logged_in=auth_service.is_logged_in(),
                         upcoming_events=upcoming_events)

@app_blueprint.route("events")
def get_events():
    # Get search and filter parameters
    search_query = request.args.get("search", "").strip()
    location_filter = request.args.get("location", "").strip()
    date_filter = request.args.get("date", "").strip()

    # Get events based on filters
    events = event_service.get_events(search_query, location_filter, date_filter)
    
    # Get unique locations for filter dropdown
    locations = event_service.get_unique_locations()

    # Build flash message for no results
    if (search_query or location_filter or date_filter) and len(events) == 0:
        filters_applied = []
        if search_query:
            filters_applied.append(f'search: "{search_query}"')
        if location_filter:
            filters_applied.append(f'location: "{location_filter}"')
        if date_filter:
            filters_applied.append(f'date: "{date_filter}"')
        
        flash(f'No events found for {", ".join(filters_applied)}.', "warning")

    return render_template("app/events.html",
                           search_query=search_query,
                           location_filter=location_filter,
                           date_filter=date_filter,
                           locations=locations,
                           events=events,
                           is_logged_in=auth_service.is_logged_in(),
                           is_participant=auth_service.is_participant(),
                           current_user_encoded_id=auth_service.get_user_resource_id())


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

        user = user_service.validate_user(email, password)

        if user:
            auth_service.login(user.id, user.global_role)
            flash("Login successful.", "success")

            # Redirect based on role
            if auth_service.is_super_admin():
                return redirect(url_for("admin.admin_dashboard", encoded_admin_id=user.encoded_user_id))
            elif auth_service.is_participant():
                return redirect(url_for("participant.dashboard", encoded_participant_id=user.encoded_user_id))
            else:
                flash("Unknown role. Contact support.", "danger")
                return redirect(url_for("app.login"))
        else:
            form_group.get("password").errors.append("Invalid email or password.")


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
        "email": FormControl(''),
        "password": FormControl(''),
        "password_confirmation": FormControl(''),
    })

    if request.method == "POST":
        first_name_input = request.form.get('first_name', '').strip()
        last_name_input = request.form.get('last_name', '').strip()
        town_input = request.form.get('town', '').strip()
        email_input = request.form.get('email', '').strip()
        password_input = request.form.get('password', '').strip()
        password_confirmation_input = request.form.get('password_confirmation', '').strip()

        form_group.get("first_name").value = first_name_input
        form_group.get("last_name").value = last_name_input
        form_group.get("town").value = town_input
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
        success = user_service.create_user(
            (first_name_input, last_name_input, town_input, normalised_email, password_hash)
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
        "current_password": FormControl(''),
        "new_password": FormControl(''),
        "confirm_password": FormControl('')
    })
    
    if request.method == "POST":
        first_name_input = request.form.get('first_name', '').strip()
        last_name_input = request.form.get('last_name', '').strip()
        town_input = request.form.get('town', '').strip()
        current_password_input = request.form.get('current_password', '').strip()
        new_password_input = request.form.get('new_password', '').strip()
        confirm_password_input = request.form.get('confirm_password', '').strip()
        
        form_group.get("first_name").value = first_name_input
        form_group.get("last_name").value = last_name_input
        form_group.get("town").value = town_input
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
    date_str = request.args.get("date", "").strip()
    formatted_date = ""
    limit = 9
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d/%m/%Y")
        except ValueError:
            formatted_date = date_str
    filter_event_results = []
    filter_group_results = []
    if filter_type == "events":
        filter_event_results = HomeService.home_filter_events(limit,location, event_type, date_str)
    elif filter_type == "groups":
        filter_group_results = HomeService.home_filter_groups()
    print("events=", filter_event_results)
    return render_template("app/search.html", events=filter_event_results, groups=filter_group_results, filter_type=filter_type, location=location,event_type=event_type,date_str =formatted_date   )

