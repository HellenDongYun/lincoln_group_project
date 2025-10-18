import time
from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
from src.app.support.support_service import SupportService
from src.app.auth.route_guard import require_login, require_support_staff
from src.app.auth.auth_service import auth_service
from src.app.common.file_service import FileService
from src.app.group.group_service import GroupService

support_blueprint = Blueprint('support', __name__, url_prefix='/support')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    #Check if file extension is allowed
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@support_blueprint.route('/new', methods=['GET', 'POST'])
@require_login
def new_request():
    #Create a new support request
    if request.method == 'POST':
        try:
            user_id = auth_service.get_user_id()
            issue_type = request.form.get('issue_type', '').strip()
            subject = request.form.get('subject', '').strip()
            description = request.form.get('description', '').strip()
            priority = request.form.get('priority', 'medium').strip()

            # Validation
            if not issue_type:
                flash("Please select an issue type.", "danger")
                return render_template('support/new_request.html', form_data=request.form)

            if not subject:
                flash("Please provide a subject.", "danger")
                return render_template('support/new_request.html', form_data=request.form)

            if not description:
                flash("Please provide a description.", "danger")
                return render_template('support/new_request.html', form_data=request.form)

            # Handle file upload
            screenshot_path = None
            if 'screenshot' in request.files:
                file = request.files['screenshot']
                if file and file.filename:
                    if allowed_file(file.filename):
                        # Use FileService to save the file
                        try:
                            filename = secure_filename(file.filename)
                            timestamp = str(int(time.time()))
                            unique_filename = f"support_{user_id}_{timestamp}_{filename}"
                            screenshot_path = FileService.save_file(file, unique_filename, 'support_screenshots')
                        except Exception as e:
                            flash(f"Error uploading screenshot: {str(e)}", "warning")
                    else:
                        flash("Invalid file type. Allowed types: png, jpg, jpeg, gif, pdf", "warning")

            # Create the support request
            request_id = SupportService.create_support_request(
                user_id, issue_type, subject, description, screenshot_path, priority
            )

            flash("Your support request has been submitted successfully. Our team will review it shortly.", "success")
            return redirect(url_for('support.view_request', request_id=request_id))

        except ValueError as e:
            flash(str(e), "danger")
            return render_template('support/new_request.html', form_data=request.form)
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            return render_template('support/new_request.html', form_data=request.form)

    # GET request
    return render_template('support/new_request.html', form_data={})


@support_blueprint.route('/my-requests')
@require_login
def my_requests():
    #View all support requests for the logged-in user
    user_id = auth_service.get_user_id()
    requests = SupportService.get_user_requests(user_id)

    return render_template('support/my_requests.html', requests=requests)

@support_blueprint.route('/request/<int:request_id>')
@require_login
def view_request(request_id):
    #View details of a specific support request
    user_id = auth_service.get_user_id()
    is_staff = auth_service.is_super_admin() or auth_service.is_support_technician()

    # Check if user can access this request
    if not SupportService.can_user_access_request(request_id, user_id, is_staff):
        flash("You do not have permission to view this support request.", "danger")
        return redirect(url_for('support.my_requests'))

    # Get request details with comments
    support_request = SupportService.get_request_details(request_id, user_id)

    if not support_request:
        flash("Support request not found.", "danger")
        return redirect(url_for('support.my_requests'))

    # Get staff list for assignment dropdown (if staff user)
    staff_list = []
    if is_staff:
        staff_list = SupportService.get_staff_list()

    return render_template('support/view_request.html',
                          support_request=support_request,
                          is_staff=is_staff,
                          staff_list=staff_list,
                          current_user_id=user_id)


@support_blueprint.route('/request/<int:request_id>/comment', methods=['POST'])
@require_login
def add_comment(request_id):
    #Add a comment to a support request

    user_id = auth_service.get_user_id()
    is_staff = auth_service.is_super_admin() or auth_service.is_support_technician()

    # Check if user can access this request
    if not SupportService.can_user_access_request(request_id, user_id, is_staff):
        flash("You do not have permission to comment on this support request.", "danger")
        return redirect(url_for('support.my_requests'))

    comment = request.form.get('comment', '').strip()

    if not comment:
        flash("Comment cannot be empty.", "danger")
        return redirect(url_for('support.view_request', request_id=request_id))

    try:
        # Add comment - mark as staff reply if user is staff
        SupportService.add_comment_to_request(request_id, user_id, comment, is_staff_reply=is_staff)
        flash("Your comment has been added.", "success")

    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for('support.view_request', request_id=request_id))

@support_blueprint.route('/queue')
@require_support_staff
def support_queue():
    #Support Queue - View all support requests (for support staff only)

    user_id = auth_service.get_user_id()
    is_group_manager = len(GroupService.get_user_managed_groups(user_id)) > 0
    is_admin_or_tech = auth_service.is_super_admin() or auth_service.is_support_technician()

    # Get filter parameters
    status_filter = request.args.get('status', '').strip() or None
    priority_filter = request.args.get('priority', '').strip() or None
    issue_type_filter = request.args.get('issue_type', '').strip() or None
    assigned_filter = request.args.get('assigned', '').strip() or None
    group_filter = request.args.get('group_filter', '').strip() or None

    # Convert 'unassigned' to None for query
    if assigned_filter == 'unassigned':
        assigned_filter = 'null'
    elif assigned_filter == 'me':
        assigned_filter = auth_service.get_user_id()

    # Get all requests based on filters
    all_requests = SupportService.get_all_requests(
        status_filter=status_filter,
        assigned_filter=None if assigned_filter == 'null' else assigned_filter,
        priority_filter=priority_filter,
        issue_type_filter=issue_type_filter
    )

    # Filter unassigned if needed
    if assigned_filter == 'null':
        all_requests = [req for req in all_requests if req.get('assigned_to') is None]

    # For Group Managers: filter to show only requests from their group members
    if is_group_manager and not is_admin_or_tech:
        managed_groups = GroupService.get_user_managed_groups(user_id)
        managed_group_ids = [g['id'] for g in managed_groups]

        # Get all members from managed groups
        group_member_ids = set()
        for group_id in managed_group_ids:
            members = GroupService.get_group_members(group_id)
            for member in members:
                member_id = member.get('user_id') or member.get('id')
                if member_id is not None:
                    group_member_ids.add(member_id)

        # Filter requests to only show those from group members
        all_requests = [req for req in all_requests if req.get('user_id') in group_member_ids]

    # Optional group filter for all support staff
    if group_filter == 'my_group' and is_group_manager:
        managed_groups = GroupService.get_user_managed_groups(user_id)
        managed_group_ids = [g['id'] for g in managed_groups]
        group_member_ids = set()
        for group_id in managed_group_ids:
            members = GroupService.get_group_members(group_id)
            for member in members:
                member_id = member.get('user_id') or member.get('id')
                if member_id is not None:
                    group_member_ids.add(member_id)
        all_requests = [req for req in all_requests if req.get('user_id') in group_member_ids]

    # Calculate statistics
    stats = {
        'total': len(all_requests),
        'new': len([r for r in all_requests if r['status'] == 'new']),
        'open': len([r for r in all_requests if r['status'] == 'open']),
        'stalled': len([r for r in all_requests if r['status'] == 'stalled']),
        'resolved': len([r for r in all_requests if r['status'] == 'resolved']),
        'unassigned': len([r for r in all_requests if r.get('assigned_to') is None])
    }

    return render_template('support/support_queue.html',
                         requests=all_requests,
                         stats=stats,
                         filters={
                             'status': status_filter or '',
                             'priority': priority_filter or '',
                             'issue_type': issue_type_filter or '',
                             'assigned': request.args.get('assigned', ''),
                             'group_filter': group_filter or ''
                         },
                         is_group_manager=is_group_manager,
                         is_admin_or_tech=is_admin_or_tech)

@support_blueprint.route('/request/<int:request_id>/take', methods=['POST'])
@require_support_staff
def take_request(request_id):
    #Take ownership of a request
    user_id = auth_service.get_user_id()

    try:
        success = SupportService.take_request(request_id, user_id)
        if success:
            flash("You have taken ownership of this request.", "success")
        else:
            flash("Unable to take this request.", "danger")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for('support.view_request', request_id=request_id))


@support_blueprint.route('/request/<int:request_id>/drop', methods=['POST'])
@require_support_staff
def drop_request(request_id):
    #Drop ownership of a request
    user_id = auth_service.get_user_id()

    try:
        success = SupportService.drop_request(request_id, user_id)
        if success:
            flash("Request has been returned to the queue.", "info")
        else:
            flash("Unable to drop this request.", "danger")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for('support.support_queue'))


@support_blueprint.route('/request/<int:request_id>/assign', methods=['POST'])
@require_support_staff
def assign_request(request_id):
    #Assign request to a staff member
    assigned_to = request.form.get('assigned_to')
    assigned_by = auth_service.get_user_id()

    if not assigned_to:
        flash("Please select a staff member.", "warning")
        return redirect(url_for('support.view_request', request_id=request_id))

    try:
        success = SupportService.assign_to_staff(request_id, int(assigned_to), assigned_by)
        if success:
            flash("Request has been assigned successfully.", "success")
        else:
            flash("Unable to assign request.", "danger")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for('support.view_request', request_id=request_id))


@support_blueprint.route('/request/<int:request_id>/update-status', methods=['POST'])
@require_support_staff
def update_status(request_id):
    #Update request status with validation
    new_status = request.form.get('status', '').strip()
    comment_text = request.form.get('comment', '').strip()
    user_id = auth_service.get_user_id()

    #Resolving requires comment
    if new_status == 'resolved' and not comment_text:
        flash("A comment is required when marking a request as resolved.", "danger")
        return redirect(url_for('support.view_request', request_id=request_id))

    try:
        # If comment provided, add it first and get comment_id
        comment_id = None
        if comment_text:
            comment_id = SupportService.add_comment_to_request(
                request_id, user_id, comment_text, is_staff_reply=True
            )

        # Update status with optional comment reference
        success = SupportService.update_status_with_comment(request_id, new_status, user_id, comment_id)

        if success:
            flash(f"Request status updated to {new_status}.", "success")
        else:
            flash("Unable to update status.", "danger")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for('support.view_request', request_id=request_id))


@support_blueprint.route('/request/<int:request_id>/reopen', methods=['POST'])
@require_login
def reopen_request(request_id):
    #Reopen a resolved request
    user_id = auth_service.get_user_id()

    try:
        success = SupportService.reopen_request(request_id, user_id)
        if success:
            flash("Request has been reopened.", "info")
        else:
            flash("Unable to reopen request.", "danger")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for('support.view_request', request_id=request_id))


@support_blueprint.route('/notifications')
@require_login
def notifications():
    #View all notifications
    user_id = auth_service.get_user_id()
    all_notifications = SupportService.get_notifications(user_id, unread_only=False)

    return render_template('support/notifications.html', notifications=all_notifications)


@support_blueprint.route('/notifications/<int:notification_id>/mark-read', methods=['POST'])
@require_login
def mark_notification_read(notification_id):
    #Mark a notification as read
    user_id = auth_service.get_user_id()

    try:
        SupportService.mark_notification_read(notification_id, user_id)
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(request.referrer or url_for('support.notifications'))
