from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from src.app.auth.auth_service import auth_service
from src.app.auth.route_guard import require_login, require_super_admin
from src.app.group.group_service import GroupService
from src.app.user.user import GroupVisibility, GroupJoinType, GroupStatus

group_blueprint = Blueprint('groups', __name__)


@group_blueprint.route('/')
def index():
    """Public discovery page for groups"""
    town_filter = request.args.get('town')
    search_term = request.args.get('search')
    
    groups = GroupService.get_public_groups_for_discovery(town_filter, search_term)
    
    return render_template('group/discover_groups.html', 
                         groups=groups, 
                         town_filter=town_filter,
                         search_term=search_term)


@group_blueprint.route('/<int:group_id>')
def view_group(group_id):
    """View group details"""
    group = GroupService.get_group_by_id(group_id)
    if not group:
        flash('Group not found', 'error')
        return redirect(url_for('groups.index'))
    
    # Check if group is private and user has access
    if group['visibility'] == 'private':
        if not auth_service.is_logged_in():
            flash('This group is private', 'error')
            return redirect(url_for('groups.index'))
        
        user_id = auth_service.get_user_id()
        if not auth_service.is_super_admin() and not GroupService.is_group_member(group_id, user_id):
            flash('You do not have access to this private group', 'error')
            return redirect(url_for('groups.index'))
    
    members = GroupService.get_group_members(group_id)
    upcoming_events = GroupService.get_group_events(group_id)
    
    # Check if current user can join/manage
    can_join = False
    is_member = False
    can_manage = False
    if auth_service.is_logged_in():
        user_id = auth_service.get_user_id()
        is_member = GroupService.is_group_member(group_id, user_id)
        can_join = not is_member and GroupService.can_user_join_group(group_id, user_id)
        can_manage = GroupService.can_user_manage_group(group_id, user_id, auth_service.is_super_admin())
    
    return render_template('group/view_group.html', 
                         group=group, 
                         members=members,
                         can_join=can_join,
                         is_member=is_member,
                         can_manage=can_manage,
                         upcoming_events=upcoming_events)


@group_blueprint.route('/<int:group_id>/join', methods=['POST'])
@require_login
def join_group(group_id):
    """Join a group"""
    user_id = auth_service.get_user_id()
    
    if not GroupService.can_user_join_group(group_id, user_id):
        flash('Unable to join this group', 'error')
        return redirect(url_for('groups.view_group', group_id=group_id))
    
    try:
        GroupService.add_member_to_group(group_id, user_id)
        flash('Successfully joined the group!', 'success')
    except Exception as e:
        flash('Error joining group', 'error')
    
    return redirect(url_for('groups.view_group', group_id=group_id))


@group_blueprint.route('/<int:group_id>/leave', methods=['POST'])
@require_login
def leave_group(group_id):
    """Leave a group"""
    user_id = auth_service.get_user_id()
    
    if not GroupService.is_group_member(group_id, user_id):
        flash('You are not a member of this group', 'error')
        return redirect(url_for('groups.view_group', group_id=group_id))
    
    try:
        GroupService.remove_member_from_group(group_id, user_id)
        flash('Successfully left the group', 'success')
    except Exception as e:
        flash('Error leaving group', 'error')
    
    return redirect(url_for('groups.index'))


@group_blueprint.route('/<int:group_id>/manage')
@require_login
def manage_group(group_id):
    """Manage group page"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()
    
    if not GroupService.can_user_manage_group(group_id, user_id, is_super_admin):
        flash('You do not have permission to manage this group', 'error')
        return redirect(url_for('groups.view_group', group_id=group_id))
    
    group = GroupService.get_group_by_id(group_id)
    members = GroupService.get_group_members(group_id)
    upcoming_events = GroupService.get_group_events(group_id)
    visibility_options = [option.value for option in GroupVisibility]
    status_options = [option.value for option in GroupStatus]
    
    return render_template('group/manage_group.html', 
                         group=group, 
                         members=members,
                         upcoming_events=upcoming_events,
                         visibility_options=visibility_options,
                         status_options=status_options,
                         is_super_admin=is_super_admin)


@group_blueprint.route('/<int:group_id>/manage/settings', methods=['POST'])
@require_super_admin
def update_group_settings(group_id):
    """Super admin can update visibility and status"""
    visibility = request.form.get('visibility')
    status = request.form.get('status')

    try:
        GroupService.update_group_settings(group_id, visibility, status)
        flash('Group settings updated successfully', 'success')
    except ValueError as error:
        flash(str(error), 'error')
    except Exception:
        flash('Failed to update group settings', 'error')

    return redirect(url_for('groups.manage_group', group_id=group_id))


@group_blueprint.route('/<int:group_id>/manage/members/<int:member_id>/role', methods=['POST'])
@require_login
def update_member_role(group_id, member_id):
    """Update a member's role in the group"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()
    
    if not GroupService.can_user_manage_group(group_id, user_id, is_super_admin):
        return jsonify({'error': 'Permission denied'}), 403
    
    new_role = request.json.get('role')
    if new_role not in ['member', 'manager']:
        return jsonify({'error': 'Invalid role'}), 400
    
    try:
        GroupService.update_member_role(group_id, member_id, new_role)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': 'Failed to update role'}), 500


@group_blueprint.route('/<int:group_id>/manage/members/<int:member_id>/remove', methods=['POST'])
@require_login
def remove_member(group_id, member_id):
    """Remove a member from the group"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()
    
    if not GroupService.can_user_manage_group(group_id, user_id, is_super_admin):
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        GroupService.remove_member_from_group(group_id, member_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': 'Failed to remove member'}), 500


@group_blueprint.route('/apply')
@require_login
def apply_for_group():
    """Form to apply for creating a new group"""
    return render_template('group/apply_group.html')


@group_blueprint.route('/apply', methods=['POST'])
@require_login
def submit_group_application():
    """Submit a group application"""
    user_id = auth_service.get_user_id()
    
    proposed_name = request.form.get('proposed_name')
    proposed_description = request.form.get('proposed_description')
    proposed_town = request.form.get('proposed_town')
    visibility = request.form.get('visibility', 'public')
    join_type = request.form.get('join_type', 'open')
    
    if not proposed_name or not proposed_town:
        flash('Name and town are required', 'error')
        return redirect(url_for('groups.apply_for_group'))
    
    try:
        GroupService.create_group_application(
            user_id, proposed_name, proposed_description, 
            proposed_town, visibility, join_type
        )
        flash('Your group application has been submitted for review', 'success')
        return redirect(url_for('groups.index'))
    except Exception as e:
        flash('Error submitting application', 'error')
        return redirect(url_for('groups.apply_for_group'))


@group_blueprint.route('/my-groups')
@require_login
def my_groups():
    """View user's groups"""
    user_id = auth_service.get_user_id()
    groups = GroupService.get_user_groups(user_id)
    managed_groups = GroupService.get_user_managed_groups(user_id)

    return render_template('group/my_groups.html', 
                         groups=groups,
                         managed_groups=managed_groups)


@group_blueprint.route('/participant-search')
@require_login
def participant_search():
    """Participant-specific search for groups and events"""
    user_id = auth_service.get_user_id()

    # Only allow participants to use this search
    if not auth_service.is_participant():
        flash('This search feature is for participants only', 'error')
        return redirect(url_for('groups.index'))

    # Extract search parameters
    search_term = request.args.get('search', '').strip()
    location_filter = request.args.get('location', '').strip()
    date_filter = request.args.get('date', '').strip()
    type_filter = request.args.get('type', '').strip()
    sort_by = request.args.get('sort', 'popularity').strip()

    # Get participant-specific search results
    try:
        results = GroupService.search_for_participants(
            user_id,
            search_term if search_term else None,
            location_filter if location_filter else None,
            date_filter if date_filter else None,
            type_filter if type_filter else None,
            sort_by
        )
    except Exception as e:
        flash('Error performing search. Please try again.', 'error')
        results = []

    # Get filter options for dropdowns
    try:
        filter_options = GroupService.get_participant_search_filter_options()
    except Exception as e:
        filter_options = {'locations': [], 'event_types': []}

    # Prepare current filters for template
    current_filters = {
        'search': search_term,
        'location': location_filter,
        'date': date_filter,
        'type': type_filter,
        'sort': sort_by
    }

    return render_template('group/participant_search.html',
                         results=results,
                         filter_options=filter_options,
                         current_filters=current_filters,
                         has_filters=bool(search_term or location_filter or date_filter or type_filter))


# Super Admin Routes
@group_blueprint.route('/admin/applications')
@require_super_admin
def admin_applications():
    """Super admin view of pending group applications"""
    applications = GroupService.get_pending_applications()
    return render_template('group/admin_applications.html', applications=applications)


@group_blueprint.route('/admin/applications/<int:application_id>/approve', methods=['POST'])
@require_super_admin
def approve_application(application_id):
    """Approve a group application"""
    decision_by = auth_service.get_user_id()
    
    try:
        group_id = GroupService.approve_group_application(application_id, decision_by)
        flash('Group application approved and group created', 'success')
    except Exception as e:
        flash('Error approving application', 'error')
    
    return redirect(url_for('groups.admin_applications'))


@group_blueprint.route('/admin/applications/<int:application_id>/reject', methods=['POST'])
@require_super_admin
def reject_application(application_id):
    """Reject a group application"""
    decision_by = auth_service.get_user_id()
    
    try:
        GroupService.reject_group_application(application_id, decision_by)
        flash('Group application rejected', 'success')
    except Exception as e:
        flash('Error rejecting application', 'error')
    
    return redirect(url_for('groups.admin_applications'))