from datetime import datetime
import math
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from src.app.group.group_service import GroupService
from src.app.auth.route_guard import require_login
from src.app.common.nav.encode import decode_id, encode_id
from src.app.participant.participant_service import ParticipantService
from src.app.auth.auth_service import AuthService


participant_blueprint = Blueprint("participant", __name__)
participant_service = ParticipantService()
auth_service = AuthService()


LEADERBOARD_TIME_WINDOWS = {
    "1month": 30,
    "3months": 90,
    "6months": 180,
    "all": None,
}


@participant_blueprint.route("/<encoded_participant_id>", methods=["GET"])
@require_login
def dashboard(encoded_participant_id: str):
    participant_id = decode_id(encoded_participant_id)

    upcoming_events = participant_service.get_upcoming_events(participant_id)
    my_registrations = participant_service.get_my_registrations(participant_id)
    my_results = participant_service.get_my_race_results(participant_id)
    
    # Get participant's group applications
    # my_applications = participant_service.get_my_applications(participant_id)
    

    rewards_snapshot = participant_service.get_rewards_dashboard(participant_id)
    earned_achievements = [
        achievement
        for achievement in rewards_snapshot["achievements"]
        if achievement.get("earned")
    ]

    next_active_challenge = next(
        (
            challenge
            for challenge in rewards_snapshot["challenges"]
            if not challenge.get("earned")
        ),
        None,
    )

    return render_template(
        "participant/participant_dashboard.html",
        upcoming_events=upcoming_events,
        my_registrations=my_registrations,
        my_results=my_results,
        participant_id=encoded_participant_id,
        rewards_summary=rewards_snapshot["summary"],
        recent_achievements=earned_achievements[:4],
        next_challenge=next_active_challenge,
    )


@participant_blueprint.route("/<encoded_participant_id>/rewards", methods=["GET"])
@require_login
def rewards(encoded_participant_id: str):
    participant_id = decode_id(encoded_participant_id)
    current_user_id = auth_service.get_user_id()

    if participant_id != current_user_id:
        flash("You can only view your own rewards dashboard.", "danger")
        if current_user_id:
            redirect_id = encode_id(current_user_id)
            return redirect(url_for("participant.dashboard", encoded_participant_id=redirect_id))
        return redirect(url_for("app.home"))

    rewards_data = participant_service.get_rewards_dashboard(participant_id)

    return render_template(
        "participant/rewards.html",
        participant_id=encoded_participant_id,
        achievements=rewards_data["achievements"],
        challenges=rewards_data["challenges"],
        summary=rewards_data["summary"],
    )


@participant_blueprint.route(
    "/<encoded_participant_id>/register/<int:event_id>", methods=["POST"]
)
@require_login
def register_for_event(encoded_participant_id: str, event_id: int):
    participant_id = decode_id(encoded_participant_id)

    current_user_id = auth_service.get_user_id()
    if participant_id != current_user_id:
        flash("You can only register for your own events.", "danger")
        return redirect(
            url_for("participant.dashboard", encoded_participant_id=encoded_participant_id)
        )

    success = participant_service.register_for_event(participant_id, event_id)

    if success:
        flash("Successfully registered for the event.", "success")
    else:
        flash("Unable to register for this event. It may be full or you may already be registered.", "danger")

    next_url = request.form.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)

    return redirect(
        url_for("participant.dashboard", encoded_participant_id=encoded_participant_id)
    )


@participant_blueprint.route(
    "/<encoded_participant_id>/cancel/<int:event_id>", methods=["POST"]
)
@require_login
def cancel_registration(encoded_participant_id: str, event_id: int):
    participant_id = decode_id(encoded_participant_id)

    current_user_id = auth_service.get_user_id()
    if participant_id != current_user_id:
        flash("You can only cancel your own registrations.", "danger")
        return redirect(
            url_for("participant.dashboard", encoded_participant_id=encoded_participant_id)
        )

    success = participant_service.cancel_registration(participant_id, event_id)
    if success:
        flash("Registration cancelled successfully.", "success")
    else:
        flash("Unable to cancel this registration.", "danger")

    next_url = request.form.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)

    return redirect(
        url_for("participant.dashboard", encoded_participant_id=encoded_participant_id)
    )


@participant_blueprint.route("/<encoded_participant_id>/applications", methods=["GET"])
@require_login
def myapplications(encoded_participant_id: str):
    participant_id = decode_id(encoded_participant_id)

    status = request.args.get("status", "all")
    page = int(request.args.get("page", 1))
    per_page = 5

    applications, total = participant_service.get_participant_applications(
        status=status,
        page=page,
        per_page=per_page,
        participant_id=participant_id,
    )
    total_pages = math.ceil(total / per_page) if per_page else 1

    return render_template(
        "participant/applications.html",
        encoded_participant_id=encoded_participant_id,
        applications=applications,
        total_pages=total_pages,
        page=page,
        per_page=per_page,
        status=status,
    )


@participant_blueprint.route(
    "/<encoded_participant_id>/applications/apply", methods=["GET", "POST"]
)
@require_login
def create_group_applyform(encoded_participant_id: str):
    participant_id = decode_id(encoded_participant_id)
    application_id = request.args.get("app_id")
    is_edit_mode = bool(application_id)
    application = None

    if is_edit_mode:
        application = participant_service.get_application_by_id(
            participant_id, application_id
        )

    if request.method == "POST":
        name = request.form.get("groupName", "").strip()
        town = request.form.get("location", "").strip()
        visibility = request.form.get("privacy", "").strip()
        description = request.form.get("description", "").strip()
        form_errors: dict[str, str] = {}

        application = {
            "proposed_name": name,
            "proposed_town": town,
            "visibility": visibility,
            "proposed_description": description,
        }

        if not name:
            form_errors["groupName"] = "Please enter a group name."
        if not town:
            form_errors["location"] = "Please enter the primary location for the group."
        if not visibility:
            form_errors["privacy"] = "Select who can discover and join your group."

        if form_errors:
            return render_template(
                "participant/create_group_form.html",
                encoded_participant_id=encoded_participant_id,
                application=application,
                is_edit_mode=is_edit_mode,
                form_errors=form_errors,
            )

        try:
            if is_edit_mode:
                participant_service.update_group_application(
                    participant_id, application_id, name, town, visibility, description
                )
                flash("Your group application has been updated successfully!", "success")
            else:
                participant_service.submit_create_group_application(
                    participant_id, name, town, visibility, description
                )
                flash("Your group application has been submitted successfully!", "success")

            return redirect(
                url_for(
                    "participant.myapplications",
                    encoded_participant_id=encoded_participant_id,
                )
            )
        except ValueError as error:
            flash(str(error), "danger")
            return render_template(
                "participant/create_group_form.html",
                encoded_participant_id=encoded_participant_id,
                application=application,
                is_edit_mode=is_edit_mode,
                form_errors=form_errors,
            )

    return render_template(
        "participant/create_group_form.html",
        encoded_participant_id=encoded_participant_id,
        application=application,
        is_edit_mode=is_edit_mode,
        form_errors={},
    )


@participant_blueprint.route(
    "/<encoded_participant_id>/applications/<application_id>/delete",
    methods=["POST"],
)
@require_login
def delete_group_application(encoded_participant_id: str, application_id: str):
    participant_id = decode_id(encoded_participant_id)
    current_user_id = auth_service.get_user_id()
    if participant_id != current_user_id:
        flash("You can only manage your own group applications.", "danger")
        if current_user_id:
            redirect_id = encode_id(current_user_id)
            return redirect(
                url_for("participant.myapplications", encoded_participant_id=redirect_id)
            )
        return redirect(url_for("app.home"))

    try:
        participant_service.delete_group_application(participant_id, application_id)
        flash("Group application deleted successfully.", "success")
    except Exception as error:
        flash(f"Error deleting group application: {error}", "danger")

    return redirect(
        url_for("participant.myapplications", encoded_participant_id=encoded_participant_id)
    )





@participant_blueprint.route("/<encoded_participant_id>/myresult")
def myresults(encoded_participant_id):
    participant_id = decode_id(encoded_participant_id)
       # get the query parameters
    search = request.args.get("search", "").strip().lower()
    date = request.args.get("date", "")
    event_type = request.args.get("type", "").strip().lower()

    # get all the data
    event_results = participant_service.get_all_eventresults_for_participant(participant_id)

    # filter data
    filtered_events = []
    for event in event_results["events"]:
        match = True

        # Search by event name
        event_name = event.get("event_name", "").lower()
        if search and search not in event_name:
            match = False

        # Filter by date
        raw_date = event.get("event_date")
        if date:
            try:
                if isinstance(raw_date, str):
                    from datetime import datetime
                    raw_date = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")  # adjust format if needed
                if raw_date.strftime("%Y-%m-%d") != date:
                    match = False
            except Exception as e:
                match = False

        # Filter by type (partial match)
        raw_type = event.get("event_type", "").lower()
        if event_type and event_type not in raw_type:
            match = False

        if match:
            filtered_events.append(event)

    event_results["events"] = filtered_events


    return render_template(
        "participant/my_result_overall.html",
        encoded_participant_id=encoded_participant_id,
        active_tab="overview",
        event_results=event_results)
    

@participant_blueprint.route("/<encoded_participant_id>/myresult/eventdetail/<event_id>")
def myresults_eventdetails(encoded_participant_id,event_id):
    tab = request.args.get('tab', 'result')
    search_name = request.args.get("search", "").lower()
    gender = request.args.get("gender")
    age_group = request.args.get("age_group")
    participant_id = decode_id(encoded_participant_id)
    all_participant_event_result = participant_service.get_participant_result_for_event(participant_id, event_id,search_name )
    event_statistics=participant_service.get_participant_result_for_event_statistics(event_id)
    participant_durations = participant_service.get_event_participant_durations(event_id,gender,age_group)
    group_by = request.args.get("group_by", "gender")  # 可选参数
    top3_grouped = participant_service.get_event_top3_grouped(event_id, group_by)
     # according to different tab render different page
    if tab == "statistics":
        return render_template(
            "participant/event_result.html",
            encoded_participant_id=encoded_participant_id,
            event_id=event_id,
            event_result=all_participant_event_result,
            active_tab="overview",
            sub_active_tab=tab,
            event_statistics=event_statistics,
            durations= participant_durations, 
            search_name=search_name,
            gender=gender,
            age_group=age_group
        )
    elif tab == "ranking":
        return render_template(
            "participant/event_result.html",
            encoded_participant_id=encoded_participant_id,
            event_id=event_id,
            event_result=all_participant_event_result,
            active_tab="overview",
            sub_active_tab=tab,
            top3_grouped=top3_grouped,
            group_by=group_by
        )
    else:  # default result page
        return render_template(
            "participant/event_result.html",
            encoded_participant_id=encoded_participant_id,
            event_result=all_participant_event_result,
            active_tab="overview",
            sub_active_tab=tab
        )


@participant_blueprint.route("/<encoded_participant_id>/resultsdetails")
def resultsdetails(encoded_participant_id):
    participant_id = decode_id(encoded_participant_id)
    # display all events list
    all_events = participant_service.get_all_events_for_participant(participant_id)

    # get current event id from query parameters
    event_id = request.args.get("event_id")
    if not event_id and all_events:
        event_id = all_events[0]["event_id"]  

    # current event
    event_detail = None
    if event_id:
        event_detail = participant_service.get_event_details_for_participant(participant_id, event_id)

    return render_template("participant/my_result_details.html", encoded_participant_id=encoded_participant_id,active_tab="details",all_events =all_events,event_detail=event_detail )


@participant_blueprint.route("/<encoded_participant_id>/resultanalysis")
def resultsanalysis(encoded_participant_id):
    participant_id = decode_id(encoded_participant_id)
    personal_event_data = participant_service.get_event_summary_split(participant_id)
    event_type = request.args.get("event_type")
    chart_data = participant_service.get_user_event_chart_data(participant_id, event_type) 
    return render_template("participant/my_result_analysis.html", encoded_participant_id=encoded_participant_id,active_tab="tags",data=personal_event_data,chart_data=chart_data,event_type=event_type)






@participant_blueprint.route("/<encoded_participant_id>/group")
def group_event_result(encoded_participant_id):
    participant_id = decode_id(encoded_participant_id)
    group_result = participant_service.get_user_group_membership_results(participant_id)
    print(group_result)
    return render_template("participant/my_result_group.html", encoded_participant_id=encoded_participant_id,active_tab="group",group_result=group_result)


# Legacy volunteer sign-up endpoints — retained as no-op JSON responses to avoid 404s
@participant_blueprint.route("/sign_task", methods=["POST"])
def sign_task_placeholder():
    return jsonify({"error": "Volunteer sign-up is not available."}), 501


@participant_blueprint.route("/cancel_role", methods=["POST"])
def cancel_role_placeholder():
    return jsonify({"error": "Volunteer cancellation is not available."}), 501


@participant_blueprint.route("/withdraw_application", methods=["POST"])
def withdraw_application_placeholder():
    return jsonify({"error": "Volunteer withdrawal is not available."}), 501


@participant_blueprint.route("/<encoded_participant_id>/leaderboard", methods=["GET"])
@require_login
def leaderboard(encoded_participant_id):
    """Display leaderboard with rankings by various metrics"""
    participant_id = decode_id(encoded_participant_id)
    
    current_user_id = auth_service.get_user_id()
    if participant_id != current_user_id:
        flash("You can only view leaderboards from your own account.", "danger")
        if current_user_id:
            redirect_id = encode_id(current_user_id)
            return redirect(url_for("participant.leaderboard", encoded_participant_id=redirect_id))
        return redirect(url_for("app.home"))
    
    # Get filter parameters
    metric = request.args.get('metric', 'events')  # events, points, volunteer
    time_filter = request.args.get('time', 'all')  # 1month, 3months, 6months, all
    group_id_param = request.args.get('group', 'all')  # 'all' or numeric id
    gender_param = (request.args.get('gender', 'all') or 'all').strip().lower()
    age_group_param = (request.args.get('age_group', 'all') or 'all').strip()

    gender_options = [
        {"value": "all", "label": "All genders"},
        {"value": "female", "label": "Female"},
        {"value": "male", "label": "Male"},
        {"value": "other", "label": "Other"},
        {"value": "unspecified", "label": "Prefer not to say"},
    ]
    valid_gender_values = {option["value"] for option in gender_options}
    if gender_param not in valid_gender_values:
        gender_param = "all"

    age_group_options = [
        {"value": "all", "label": "All age groups"},
        {"value": "Under 18", "label": "Under 18"},
        {"value": "18-29", "label": "18-29"},
        {"value": "30-44", "label": "30-44"},
        {"value": "45+", "label": "45+"},
        {"value": "prefer_not_to_say", "label": "Prefer not to say"},
    ]
    valid_age_group_values = {option["value"] for option in age_group_options}
    if age_group_param not in valid_age_group_values:
        age_group_param = "all"
    
    # Validate metric
    if metric not in ['events', 'points', 'volunteer']:
        metric = 'events'
    
    # Map time filter to days
    time_window_days = LEADERBOARD_TIME_WINDOWS.get(time_filter)
    
    # Resolve group filter
    selected_group_id = None
    user_groups = []
    try:
        user_groups = GroupService.get_user_groups(participant_id) or []
    except Exception:
        user_groups = []

    if group_id_param and group_id_param != 'all':
        try:
            selected_group_id = int(group_id_param)
            # Validate user membership for safety; allow managers/members
            is_member = any(g.get('id') == selected_group_id for g in user_groups)
            if not is_member:
                flash('You do not belong to the selected group.', 'warning')
                selected_group_id = None
                group_id_param = 'all'
        except ValueError:
            selected_group_id = None
            group_id_param = 'all'

    gender_value = None
    if gender_param == 'unspecified':
        gender_value = 'unspecified'
    elif gender_param != 'all':
        gender_value = gender_param

    age_group_value = None
    if age_group_param == 'prefer_not_to_say':
        age_group_value = 'Unknown'
    elif age_group_param != 'all':
        age_group_value = age_group_param

    # Get leaderboard data
    leaderboard_data = participant_service.get_leaderboard_data(
        metric=metric,
        time_window_days=time_window_days,
        current_user_id=participant_id,
        group_id=selected_group_id,
        gender=gender_value,
        age_group=age_group_value
    )
    
    return render_template(
        "participant/leaderboard.html",
        encoded_participant_id=encoded_participant_id,
        leaderboard=leaderboard_data,
        current_metric=metric,
        current_time_filter=time_filter,
        time_windows=LEADERBOARD_TIME_WINDOWS,
        groups=user_groups,
        current_group=group_id_param,
        gender_options=gender_options,
        current_gender=gender_param,
        age_group_options=age_group_options,
        current_age_group=age_group_param
    )

