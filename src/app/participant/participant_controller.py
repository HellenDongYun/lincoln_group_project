from datetime import datetime
import math
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify

from src.app.auth.route_guard import require_login
from src.app.common.nav.encode import decode_id, encode_id
from src.app.participant.participant_service import ParticipantService
from src.app.auth.auth_service import AuthService


participant_blueprint = Blueprint("participant", __name__)
participant_service = ParticipantService()
auth_service = AuthService()


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
        name = request.form.get("groupName")
        town = request.form.get("location")
        visibility = request.form.get("privacy")
        description = request.form.get("description")

        application = {
            "proposed_name": name,
            "proposed_town": town,
            "visibility": visibility,
            "proposed_description": description,
        }

        if not name or not town or not visibility:
            flash(
                "Please fill in all required fields: group name, location, and visibility.",
                "danger",
            )
            return render_template(
                "participant/create_group_form.html",
                encoded_participant_id=encoded_participant_id,
                application=application,
                is_edit_mode=is_edit_mode,
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

