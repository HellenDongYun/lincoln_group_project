
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
import math

from src.app.auth.route_guard import require_login
from src.app.common.nav.encode import decode_id
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

    return render_template(
        "participant/participant_dashboard.html",
        upcoming_events=upcoming_events,
        my_registrations=my_registrations,
        my_results=my_results,
        participant_id=encoded_participant_id,
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
        flash("Successfully registered for the event!", "success")
    else:
        flash("Unable to register for this event. It may be full or already registered.", "danger")

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

    try:
        participant_service.delete_group_application(participant_id, application_id)
        flash("Group application deleted successfully.", "success")
    except Exception as error:
        flash(f"Error deleting group application: {error}", "danger")

    return redirect(
        url_for("participant.myapplications", encoded_participant_id=encoded_participant_id)
    )


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

