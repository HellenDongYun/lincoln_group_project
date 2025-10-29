from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session
from werkzeug.utils import secure_filename

from src.app.auth.auth_service import auth_service
from src.app.auth.route_guard import require_super_admin, require_volunteer_or_manager
from src.app.common.uploads import is_allowed_file
from src.app.results.results_service import ResultsService

results_service = ResultsService()
results_blueprint = Blueprint('results', __name__)

# Allowed file extensions for CSV upload
ALLOWED_EXTENSIONS = {'csv'}


@results_blueprint.route("/", methods=["GET"])
def public_results():
    """Public page to view all race results"""
    # Get all events with results
    events_with_results = results_service.get_events_with_results()
    
    # Get selected event results if event_id is provided
    selected_event_id = request.args.get('event_id', type=int)
    selected_event = None
    results = []
    
    if selected_event_id:
        selected_event = results_service.get_event_details(selected_event_id)
        results = results_service.get_event_results(selected_event_id)
    
    return render_template("results/results.html", 
                         events_with_results=events_with_results,
                         selected_event=selected_event,
                         results=results,
                         selected_event_id=selected_event_id)


@results_blueprint.route("/upload", methods=["GET", "POST"])
@require_volunteer_or_manager
def upload_results():
    """Upload CSV results - admins and volunteers only"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()

    if request.method == "GET":
        # Get all events for the dropdown
        events = results_service.get_all_events(user_id=user_id, is_super_admin=is_super_admin)
        return render_template("results/upload.html", events=events)
    
    # Handle POST request - file upload
    event_id_raw = request.form.get('event_id')
    overwrite = request.form.get('overwrite', 'false').lower() == 'true'

    if not event_id_raw:
        flash("Please select an event.", "danger")
        return redirect(url_for('results.upload_results'))

    try:
        event_id = int(event_id_raw)
    except (TypeError, ValueError):
        flash("Invalid event selection.", "danger")
        return redirect(url_for('results.upload_results'))

    has_access, error_message = results_service.validate_event_access(
        event_id, user_id=user_id, is_super_admin=is_super_admin
    )
    if not has_access:
        flash(error_message, "danger")
        return redirect(url_for('results.upload_results'))

    if 'results_file' not in request.files:
        flash("No file selected.", "danger")
        return redirect(url_for('results.upload_results'))
    
    file = request.files['results_file']
    
    if file.filename == '':
        flash("No file selected.", "danger")
        return redirect(url_for('results.upload_results'))
    
    if file and is_allowed_file(file.filename, ALLOWED_EXTENSIONS):
        try:
            # Read and process CSV file
            filename = secure_filename(file.filename)
            csv_content = file.read().decode('utf-8')
            
            # Process the CSV data
            success, message, stats = results_service.process_csv_results(event_id, csv_content, overwrite)
            
            # Store processing statistics in session for display
            session['processing_stats'] = stats
            session['processing_message'] = message
            session['processing_success'] = success
            
            if success:
                if stats.get('errors', 0) > 0:
                    # Had some issues but still processed successfully
                    flash(message, "warning")
                else:
                    # Complete success
                    flash(message, "success")
                return redirect(url_for('results.public_results', event_id=event_id))
            else:
                # Check if this is unregistered participant confirmation needed
                if message == "UNREGISTERED_CONFIRMATION":
                    # Store file content temporarily for confirmation
                    session['pending_upload'] = {
                        'event_id': event_id,
                        'csv_content': csv_content,
                        'filename': filename
                    }
                    
                    # Get event details for display
                    event = results_service.get_event_details(event_id)
                    
                    return render_template("results/upload.html",
                                         events=events,
                                         unregistered_confirmation_needed=True,
                                         selected_event=event,
                                         stats=stats,
                                         message="Some participants in your CSV are not registered for this event.")
                
                # Check if this is an overwrite confirmation needed
                elif "already has" in message and "confirm overwrite" in message:
                    # Get event details and existing result summary for confirmation
                    event = results_service.get_event_details(event_id)
                    existing_summary = results_service.get_event_result_summary(event_id)
                    
                    # Store file content temporarily in session for confirmation
                    session['pending_upload'] = {
                        'event_id': event_id,
                        'csv_content': csv_content,
                        'filename': filename
                    }
                    
                    return render_template("results/upload.html",
                                         events=events,
                                         confirmation_needed=True,
                                         selected_event=event,
                                         existing_summary=existing_summary,
                                         message=message)
                else:
                    # Other validation errors - show detailed error information
                    return render_template("results/upload.html",
                                         events=events,
                                         stats=stats,
                                         selected_event_id=event_id,
                                         error_message=message)
                    
        except Exception as e:
            flash(f"Error reading CSV file: {str(e)}", "danger")
    else:
        flash("Please upload a valid CSV file.", "danger")
    
    return redirect(url_for('results.upload_results'))


@results_blueprint.route("/upload/confirm", methods=["POST"])
@require_volunteer_or_manager
def confirm_overwrite():
    """Confirm overwriting existing results"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()

    action = request.form.get('action')
    
    if action == 'confirm' and 'pending_upload' in session:
        pending = session['pending_upload']
        event_id = int(pending['event_id'])
        csv_content = pending['csv_content']

        has_access, error_message = results_service.validate_event_access(
            event_id, user_id=user_id, is_super_admin=is_super_admin
        )
        if not has_access:
            flash(error_message, "danger")
            session.pop('pending_upload', None)
            return redirect(url_for('results.upload_results'))
        
        # Process with overwrite=True
        success, message, stats = results_service.process_csv_results(
            event_id, csv_content, overwrite=True
        )
        
        # Store processing statistics in session for banner display
        session['processing_stats'] = stats
        session['processing_message'] = message
        session['processing_success'] = success
        
        # Clear pending upload from session
        session.pop('pending_upload', None)
        
        if success:
            if stats['errors'] > 0:
                flash(message, "warning")
            else:
                flash(message, "success")
            return redirect(url_for('results.public_results', event_id=event_id))
        else:
            flash(f"Error processing CSV: {message}", "danger")
    else:
        # Cancel - clear pending upload
        session.pop('pending_upload', None)
        flash("Upload cancelled.", "info")
    
    return redirect(url_for('results.upload_results'))


@results_blueprint.route("/upload/confirm_unregistered", methods=["POST"])
@require_volunteer_or_manager
def confirm_unregistered():
    """Handle unregistered participant confirmation"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()

    action = request.form.get('action')
    
    if action == 'proceed_registered_only' and 'pending_upload' in session:
        pending = session['pending_upload']
        event_id = int(pending['event_id'])
        csv_content = pending['csv_content']

        has_access, error_message = results_service.validate_event_access(
            event_id, user_id=user_id, is_super_admin=is_super_admin
        )
        if not has_access:
            flash(error_message, "danger")
            session.pop('pending_upload', None)
            return redirect(url_for('results.upload_results'))
        
        # Process with unregistered participants excluded
        success, message, stats = results_service.process_csv_results_with_unregistered(
            event_id, csv_content, overwrite=False, include_unregistered=False
        )
        
        # Store processing statistics in session
        session['processing_stats'] = stats
        session['processing_message'] = message
        session['processing_success'] = success
        
        # Clear pending upload from session
        session.pop('pending_upload', None)
        
        if success:
            flash(message, "success")
            return redirect(url_for('results.public_results', event_id=event_id))
        else:
            flash(f"Error processing CSV: {message}", "danger")
            
    elif action == 'proceed_include_all' and 'pending_upload' in session:
        pending = session['pending_upload']
        event_id = int(pending['event_id'])
        csv_content = pending['csv_content']

        has_access, error_message = results_service.validate_event_access(
            event_id, user_id=user_id, is_super_admin=is_super_admin
        )
        if not has_access:
            flash(error_message, "danger")
            session.pop('pending_upload', None)
            return redirect(url_for('results.upload_results'))
        
        # Process including unregistered participants
        success, message, stats = results_service.process_csv_results_with_unregistered(
            event_id, csv_content, overwrite=False, include_unregistered=True
        )
        
        # Store processing statistics in session
        session['processing_stats'] = stats
        session['processing_message'] = message
        session['processing_success'] = success
        
        # Clear pending upload from session
        session.pop('pending_upload', None)
        
        if success:
            flash(message, "warning")  # Warning because we included unregistered
            return redirect(url_for('results.public_results', event_id=event_id))
        else:
            flash(f"Error processing CSV: {message}", "danger")
    else:
        # Cancel - clear pending upload
        session.pop('pending_upload', None)
        flash("Upload cancelled.", "info")
    
    return redirect(url_for('results.upload_results'))


@results_blueprint.route("/remove/<int:event_id>", methods=["POST"])
@require_super_admin
def remove_results(event_id):
    """Remove all results for an event"""
    try:
        removed_count = results_service.remove_event_results(event_id)
        
        if removed_count > 0:
            flash(f"Successfully removed {removed_count} race results.", "success")
        else:
            flash("No results found to remove.", "info")
            
    except Exception as e:
        flash(f"Error removing results: {str(e)}", "danger")
    
    return redirect(url_for('results.public_results'))


@results_blueprint.route("/record", methods=["GET", "POST"])
@require_volunteer_or_manager
def record_time():
    """Record completion time by participant ID - volunteers and managers only"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()

    if request.method == "GET":
        # Get all events for the dropdown
        events = results_service.get_all_events(user_id=user_id, is_super_admin=is_super_admin)
        return render_template("results/record_time.html", events=events)

    # Handle POST request - manual time recording
    event_id_raw = request.form.get('event_id')
    participant_id = request.form.get('participant_id')
    participant_email = request.form.get('participant_email')
    completion_time = request.form.get('completion_time')

    if not event_id_raw:
        flash("Please select an event.", "danger")
        return redirect(url_for('results.record_time'))

    try:
        event_id = int(event_id_raw)
    except (TypeError, ValueError):
        flash("Invalid event selection.", "danger")
        return redirect(url_for('results.record_time'))

    if not participant_id and not participant_email:
        flash("Please enter either a participant User ID or email address.", "danger")
        return redirect(url_for('results.record_time'))

    if not completion_time:
        flash("Please enter the completion time.", "danger")
        return redirect(url_for('results.record_time'))

    # Convert participant_id to int if provided, otherwise lookup by email
    if participant_id:
        try:
            participant_id = int(participant_id.strip())
        except ValueError:
            flash("Invalid participant ID format. Please enter a valid number.", "danger")
            return redirect(url_for('results.record_time'))
    elif participant_email:
        participant_email = participant_email.strip()
        if not participant_email:
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for('results.record_time'))

    try:
        has_access, error_message = results_service.validate_event_access(
            event_id, user_id=user_id, is_super_admin=is_super_admin
        )
        if not has_access:
            flash(error_message, "danger")
            return redirect(url_for('results.record_time'))

        # Record the completion time using provided time
        success, message = results_service.record_completion_time(event_id, participant_id, participant_email, completion_time)

        if success:
            flash(message, "success")
            return redirect(url_for('results.public_results', event_id=event_id))
        else:
            flash(message, "danger")

    except Exception as e:
        flash(f"Error recording completion time: {str(e)}", "danger")

    return redirect(url_for('results.record_time'))


@results_blueprint.route("/api/event/<int:event_id>/results", methods=["GET"])
def api_event_results(event_id):
    """API endpoint to get results for a specific event (JSON)"""
    results = results_service.get_event_results(event_id)
    event = results_service.get_event_details(event_id)

    return jsonify({
        'event': event,
        'results': results
    })
