from datetime import datetime
from itertools import zip_longest

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from src.app.auth.auth_service import auth_service
from src.app.auth.route_guard import require_login, require_super_admin
from src.app.group.group_service import GroupService
from src.app.user.user import GroupVisibility, GroupStatus
from src.app.common.nav.encode import encode_id

group_blueprint = Blueprint('groups', __name__)


def _group_landing_url():
    """Return the default landing page for group redirects."""
    if auth_service.is_logged_in():
        if auth_service.is_participant():
            return url_for('groups.participant_search')
        return url_for('groups.my_groups')
    return url_for('app.home_filter_events', filter_type='groups')


@group_blueprint.route('/<int:group_id>')
def view_group(group_id):
    """View group details"""
    group = GroupService.get_group_by_id(group_id)
    if not group:
        flash('Group not found', 'error')
        return redirect(_group_landing_url())
    
    # Check if group is private and user has access
    if group['visibility'] == 'private':
        if not auth_service.is_logged_in():
            flash('This group is private', 'error')
            return redirect(_group_landing_url())
        
        user_id = auth_service.get_user_id()
        if not auth_service.is_super_admin() and not GroupService.is_group_member(group_id, user_id):
            flash('You do not have access to this private group', 'error')
            return redirect(_group_landing_url())
    
    members = GroupService.get_group_members(group_id)

    current_user_id = auth_service.get_user_id() if auth_service.is_logged_in() else None
    current_user_encoded_id = encode_id(current_user_id) if current_user_id else None

    # Check if current user can join/manage
    can_join = False
    is_member = False
    can_manage = False
    if auth_service.is_logged_in():
        user_id = current_user_id
        is_member = GroupService.is_group_member(group_id, user_id)
        can_join = not is_member and GroupService.can_user_join_group(
            group_id, user_id, is_super_admin=auth_service.is_super_admin()
        )
        can_manage = GroupService.can_user_manage_group(group_id, user_id, auth_service.is_super_admin())
        upcoming_events = GroupService.get_group_events(
            group_id,
            current_user_id=user_id,
            user_is_member=is_member
        )
    else:
        upcoming_events = GroupService.get_group_events(group_id)

    return render_template('group/view_group.html', 
                         group=group, 
                         members=members,
                         can_join=can_join,
                         is_member=is_member,
                         can_manage=can_manage,
                         upcoming_events=upcoming_events,
                         current_user_encoded_id=current_user_encoded_id)


@group_blueprint.route('/<int:group_id>/join', methods=['POST'])
@require_login
def join_group(group_id):
    """Join a group"""
    user_id = auth_service.get_user_id()
    next_url = (request.form.get('next') or '').strip()
    redirect_target = url_for('groups.view_group', group_id=group_id)
    if next_url.startswith('/'):
        redirect_target = next_url

    group = GroupService.get_group_by_id(group_id)

    if not group:
        flash('Group not found or unavailable.', 'error')
        return redirect(_group_landing_url())

    visibility = str(group.get('visibility') or '').strip().lower()

    if GroupService.is_group_member(group_id, user_id):
        flash('You are already a member of this group.', 'info')
        return redirect(redirect_target)

    if visibility != 'public' and not auth_service.is_super_admin():
        flash('This group requires a request to join.', 'warning')
        return redirect(redirect_target)

    try:
        GroupService.add_member_to_group(group_id, user_id)
        flash('Successfully joined the group!', 'success')
    except Exception:
        flash('Error joining group. Please try again later.', 'error')

    return redirect(redirect_target)


@group_blueprint.route('/<int:group_id>/events/<int:event_id>/volunteer/<int:role_id>', methods=['POST'])
@require_login
def volunteer_for_role(group_id, event_id, role_id):
    """Allow a group member to volunteer for a role at an event"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()

    if not (GroupService.is_group_member(group_id, user_id) or is_super_admin):
        flash('Join this group to volunteer for its events.', 'warning')
        return redirect(url_for('groups.view_group', group_id=group_id))

    try:
        GroupService.assign_event_volunteer(group_id, event_id, user_id, role_id)
        flash('Thanks for volunteering! You are assigned to this role.', 'success')
    except ValueError as exc:
        flash(str(exc), 'warning')
    except Exception as exc:
        current_app.logger.exception('Failed to assign volunteer role: %s', exc)
        flash('Unable to sign up for that volunteer role right now.', 'error')

    return redirect(url_for('groups.view_group', group_id=group_id))


@group_blueprint.route('/<int:group_id>/events/<int:event_id>/volunteer/<int:role_id>/cancel', methods=['POST'])
@require_login
def cancel_volunteer_role(group_id, event_id, role_id):
    """Allow a volunteer to cancel their role assignment"""
    user_id = auth_service.get_user_id()

    try:
        GroupService.remove_event_volunteer(group_id, event_id, user_id, role_id)
        flash('Your volunteer role has been released.', 'info')
    except ValueError as exc:
        flash(str(exc), 'warning')
    except Exception as exc:
        current_app.logger.exception('Failed to cancel volunteer role: %s', exc)
        flash('Unable to cancel that volunteer role right now.', 'error')

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

    return redirect(url_for('groups.my_groups'))


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
    challenges = GroupService.get_group_challenges(group_id)
    challenge_options = GroupService.get_group_challenge_options(group_id)
    visibility_options = [option.value for option in GroupVisibility]
    status_options = [option.value for option in GroupStatus]

    event_assignments = {}
    event_assignment_list = []

    for event in upcoming_events:
        payload = _build_event_assignment_payload(group_id, event.id)
        event_assignments[event.id] = payload
        event_assignment_list.append(payload)
    
    return render_template('group/manage_group.html', 
                         group=group, 
                         members=members,
                         upcoming_events=upcoming_events,
                         challenges=challenges,
                         visibility_options=visibility_options,
                         status_options=status_options,
                         is_super_admin=is_super_admin,
                         event_assignments=event_assignments,
                         event_assignment_json=event_assignment_list,
                         group_members_json=members,
                         manager_dashboard_url=url_for('groups.manager_dashboard', group_id=group_id),
                         challenge_options=challenge_options)


@group_blueprint.route('/manager/dashboard')
@require_login
def manager_dashboard():
    """Analytics-focused dashboard for group managers"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()

    managed_groups = GroupService.get_user_managed_groups(user_id)
    managed_group_ids = {group['id'] for group in managed_groups}

    requested_group_id = request.args.get('group_id', type=int)
    events_scope = request.args.get('events', 'upcoming')
    if events_scope not in {'upcoming', 'all'}:
        events_scope = 'upcoming'
    include_past_events = events_scope == 'all'
    selected_group_id = requested_group_id

    if not selected_group_id:
        if managed_groups:
            selected_group_id = managed_groups[0]['id']
        elif is_super_admin:
            # Allow super admins to target a group via query parameter only
            flash('Select a group to view analytics.', 'info')
            return redirect(_group_landing_url())
        else:
            flash('You do not manage any groups yet.', 'warning')
            return redirect(_group_landing_url())

    if not is_super_admin and selected_group_id not in managed_group_ids:
        flash('You do not have access to that group dashboard.', 'error')
        return redirect(_group_landing_url())

    group = GroupService.get_group_by_id(selected_group_id)
    if not group:
        flash('Group not found.', 'error')
        return redirect(_group_landing_url())

    dashboard = GroupService.get_manager_dashboard_snapshot(selected_group_id, include_past_events)

    return render_template('group/manager_dashboard.html',
                           group=group,
                           dashboard=dashboard,
                           managed_groups=managed_groups,
                           selected_group_id=selected_group_id,
                           events_scope=events_scope,
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


@group_blueprint.route('/<int:group_id>/events/new', methods=['GET', 'POST'])
@require_login
def create_group_event(group_id):
    """Group managers can create new events for their community"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()

    if not GroupService.can_user_manage_group(group_id, user_id, is_super_admin):
        flash('You do not have permission to create events for this group', 'error')
        return redirect(url_for('groups.view_group', group_id=group_id))

    group = GroupService.get_group_by_id(group_id)
    if not group:
        flash('Group not found', 'error')
        return redirect(_group_landing_url())
    volunteer_roles = GroupService.get_all_volunteer_roles()
    form_data = _initial_event_form_data()

    if request.method == 'POST':
        form_data = _initial_event_form_data()  # reset defaults
        form_data.update(_extract_event_form_submission())
        errors, event_payload = _validate_event_form(form_data)

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('group/event_form.html',
                                   group=group,
                                   form_data=form_data,
                                   volunteer_roles=volunteer_roles,
                                   is_edit=False,
                                   page_title='Create event',
                                   submit_label='Create event')

        try:
            event_id = GroupService.create_group_event(group_id, user_id, **event_payload)
            flash('Event created successfully.', 'success')
            current_app.logger.info('Group %s created event %s', group_id, event_id)
            return redirect(url_for('groups.manage_group', group_id=group_id))
        except Exception as exc:
            current_app.logger.exception('Failed to create event: %s', exc)
            flash('Failed to create event. Please try again.', 'error')

    return render_template('group/event_form.html',
                           group=group,
                           form_data=form_data,
               volunteer_roles=volunteer_roles,
                           is_edit=False,
                           page_title='Create event',
                           submit_label='Create event')


@group_blueprint.route('/<int:group_id>/events/<int:event_id>/edit', methods=['GET', 'POST'])
@require_login
def edit_group_event(group_id, event_id):
    """Group managers can edit existing events"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()

    if not GroupService.can_user_manage_group(group_id, user_id, is_super_admin):
        flash('You do not have permission to edit events for this group', 'error')
        return redirect(url_for('groups.view_group', group_id=group_id))

    group = GroupService.get_group_by_id(group_id)
    if not group:
        flash('Group not found', 'error')
        return redirect(_group_landing_url())
    event = GroupService.get_group_event(group_id, event_id)

    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('groups.manage_group', group_id=group_id))

    volunteer_roles = GroupService.get_all_volunteer_roles()
    assigned_requirements = GroupService.get_event_volunteer_requirements(event_id)
    form_data = _initial_event_form_data(event, assigned_requirements)

    if request.method == 'POST':
        submitted = _extract_event_form_submission()
        for key, value in submitted.items():
            form_data[key] = value
        errors, event_payload = _validate_event_form(form_data)

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('group/event_form.html',
                                   group=group,
                                   form_data=form_data,
                                   volunteer_roles=volunteer_roles,
                                   is_edit=True,
                                   page_title='Edit event',
                                   submit_label='Save changes')

        try:
            GroupService.update_group_event(group_id, event_id, **event_payload)
            notified = _notify_event_participants(event_id,
                                                 f"Event '{event_payload['name']}' has been updated. Please review the latest details.")
            if notified:
                flash(f'Event updated and {notified} participant{"s" if notified != 1 else ""} notified.', 'success')
            else:
                flash('Event updated successfully.', 'success')
            return redirect(url_for('groups.manage_group', group_id=group_id))
        except Exception as exc:
            current_app.logger.exception('Failed to update event: %s', exc)
            flash('Failed to update event. Please try again.', 'error')

    return render_template('group/event_form.html',
                           group=group,
                           form_data=form_data,
               volunteer_roles=volunteer_roles,
                           is_edit=True,
                           page_title='Edit event',
                           submit_label='Save changes')


@group_blueprint.route('/<int:group_id>/events/<int:event_id>/cancel', methods=['POST'])
@require_login
def cancel_group_event(group_id, event_id):
    """Group managers can cancel (delete) their events"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()

    if not GroupService.can_user_manage_group(group_id, user_id, is_super_admin):
        flash('You do not have permission to cancel this event', 'error')
        return redirect(url_for('groups.view_group', group_id=group_id))

    event = GroupService.get_group_event(group_id, event_id)
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('groups.manage_group', group_id=group_id))

    participants = GroupService.get_event_participants(event_id)

    try:
        removed = GroupService.cancel_group_event(group_id, event_id)
        if removed:
            notified = _notify_event_participants(event_id,
                                                 f"Event '{event.name}' has been cancelled.",
                                                 participants)
            if notified:
                flash(f'Event cancelled. {notified} participant{"s" if notified != 1 else ""} notified.', 'warning')
            else:
                flash('Event cancelled successfully.', 'warning')
        else:
            flash('Unable to cancel event.', 'error')
    except Exception as exc:
        current_app.logger.exception('Failed to cancel event: %s', exc)
        flash('Failed to cancel event. Please try again.', 'error')

    return redirect(url_for('groups.manage_group', group_id=group_id))


@group_blueprint.route('/<int:group_id>/challenges', methods=['POST'])
@require_login
def create_group_challenge(group_id):
    """Create a new challenge for the group"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()
    manage_url = url_for('groups.manage_group', group_id=group_id) + '#challenges'

    if not GroupService.can_user_manage_group(group_id, user_id, is_super_admin):
        flash('You do not have permission to manage challenges for this group.', 'error')
        return redirect(manage_url)

    errors, payload = GroupService.validate_challenge_form(request.form)
    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(manage_url)

    try:
        GroupService.create_group_challenge(group_id, user_id, payload)
        flash('Challenge created successfully.', 'success')
    except Exception as exc:
        current_app.logger.exception('Failed to create group challenge: %s', exc)
        flash('Failed to create challenge. Please try again.', 'error')

    return redirect(manage_url)


@group_blueprint.route('/<int:group_id>/challenges/<int:challenge_id>/update', methods=['POST'])
@require_login
def update_group_challenge(group_id, challenge_id):
    """Update an existing challenge"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()
    manage_url = url_for('groups.manage_group', group_id=group_id) + '#challenges'

    if not GroupService.can_user_manage_group(group_id, user_id, is_super_admin):
        flash('You do not have permission to manage challenges for this group.', 'error')
        return redirect(manage_url)

    errors, payload = GroupService.validate_challenge_form(request.form)
    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(manage_url)

    try:
        GroupService.update_group_challenge(group_id, challenge_id, payload)
        flash('Challenge updated successfully.', 'success')
    except ValueError as error:
        flash(str(error), 'error')
    except Exception as exc:
        current_app.logger.exception('Failed to update group challenge: %s', exc)
        flash('Failed to update challenge. Please try again.', 'error')

    return redirect(manage_url)


@group_blueprint.route('/<int:group_id>/challenges/<int:challenge_id>/delete', methods=['POST'])
@require_login
def delete_group_challenge(group_id, challenge_id):
    """Delete a challenge"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()
    manage_url = url_for('groups.manage_group', group_id=group_id) + '#challenges'

    if not GroupService.can_user_manage_group(group_id, user_id, is_super_admin):
        flash('You do not have permission to manage challenges for this group.', 'error')
        return redirect(manage_url)

    try:
        GroupService.delete_group_challenge(group_id, challenge_id)
        flash('Challenge deleted.', 'warning')
    except ValueError as error:
        flash(str(error), 'error')
    except Exception as exc:
        current_app.logger.exception('Failed to delete group challenge: %s', exc)
        flash('Failed to delete challenge. Please try again.', 'error')

    return redirect(manage_url)


def _build_event_assignment_payload(group_id, event_id):
    snapshot = GroupService.get_event_assignment_snapshot(group_id, event_id)
    event_obj = snapshot.get('event')

    event_datetime = None
    if event_obj is None:
        event_meta = {
            'id': event_id,
            'name': '',
            'datetime': None,
            'datetime_display': '',
            'town': '',
            'visibility': '',
            'max_participants': None
        }
    elif isinstance(event_obj, dict):
        event_datetime = event_obj.get('datetime')
        event_meta = {
            'id': event_obj.get('id') or event_id,
            'name': event_obj.get('name', ''),
            'datetime': event_datetime.isoformat() if hasattr(event_datetime, 'isoformat') else event_datetime,
            'datetime_display': event_obj.get('datetime_display') or _format_event_datetime(event_datetime),
            'town': event_obj.get('town', ''),
            'visibility': event_obj.get('visibility', ''),
            'max_participants': event_obj.get('max_participants')
        }
    else:
        event_datetime = getattr(event_obj, 'datetime', None)
        event_meta = {
            'id': getattr(event_obj, 'id', event_id),
            'name': getattr(event_obj, 'name', ''),
            'datetime': event_datetime.isoformat() if hasattr(event_datetime, 'isoformat') else event_datetime,
            'datetime_display': getattr(event_obj, 'datetime_str', None) or _format_event_datetime(event_datetime),
            'town': getattr(event_obj, 'town', ''),
            'visibility': getattr(event_obj, 'visibility', ''),
            'max_participants': getattr(event_obj, 'max_participants', None)
        }

    max_participants = event_meta['max_participants']
    if max_participants is not None:
        try:
            max_participants = int(max_participants)
        except (TypeError, ValueError):
            max_participants = None
    event_meta['max_participants'] = max_participants

    return {
        'event': event_meta,
        'participants': snapshot.get('participants', []),
        'volunteer_requirements': snapshot.get('volunteer_requirements', []),
        'volunteer_assignments': snapshot.get('volunteer_assignments', [])
    }


def _format_event_datetime(value):
    if not value:
        return ''
    if hasattr(value, 'strftime'):
        try:
            from src.app.common.datetime_format import DatetimeFormat
            return value.strftime(DatetimeFormat.NZ_SHORT_DATETIME.value)
        except Exception:
            return value.strftime('%Y-%m-%d %H:%M')
    return str(value)


@group_blueprint.route('/<int:group_id>/events/<int:event_id>/participants', methods=['POST'])
@require_login
def assign_event_participant(group_id, event_id):
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()

    if not GroupService.can_user_manage_group(group_id, user_id, is_super_admin):
        return jsonify({'error': 'Permission denied'}), 403

    payload = request.get_json(silent=True) or {}
    member_id = payload.get('member_id')

    try:
        member_id = int(member_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid member'}), 400

    try:
        GroupService.assign_event_participant(group_id, event_id, member_id)
        assignments = _build_event_assignment_payload(group_id, event_id)
        return jsonify({'success': True, 'assignments': assignments})
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except Exception as exc:
        current_app.logger.exception('Failed to assign participant: %s', exc)
        return jsonify({'error': 'Failed to assign participant'}), 500


@group_blueprint.route('/<int:group_id>/events/<int:event_id>/participants/remove', methods=['POST'])
@require_login
def remove_event_participant(group_id, event_id):
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()

    if not GroupService.can_user_manage_group(group_id, user_id, is_super_admin):
        return jsonify({'error': 'Permission denied'}), 403

    payload = request.get_json(silent=True) or {}
    member_id = payload.get('member_id')

    try:
        member_id = int(member_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid member'}), 400

    try:
        GroupService.remove_event_participant(group_id, event_id, member_id)
        assignments = _build_event_assignment_payload(group_id, event_id)
        return jsonify({'success': True, 'assignments': assignments})
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except Exception as exc:
        current_app.logger.exception('Failed to remove participant: %s', exc)
        return jsonify({'error': 'Failed to remove participant'}), 500


@group_blueprint.route('/<int:group_id>/events/<int:event_id>/volunteers', methods=['POST'])
@require_login
def assign_event_volunteer(group_id, event_id):
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()

    if not GroupService.can_user_manage_group(group_id, user_id, is_super_admin):
        return jsonify({'error': 'Permission denied'}), 403

    payload = request.get_json(silent=True) or {}
    member_id = payload.get('member_id')
    role_id = payload.get('role_id')

    try:
        member_id = int(member_id)
        role_id = int(role_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid assignment payload'}), 400

    try:
        GroupService.assign_event_volunteer(group_id, event_id, member_id, role_id)
        assignments = _build_event_assignment_payload(group_id, event_id)
        return jsonify({'success': True, 'assignments': assignments})
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except Exception as exc:
        current_app.logger.exception('Failed to assign volunteer: %s', exc)
        return jsonify({'error': 'Failed to assign volunteer'}), 500


@group_blueprint.route('/<int:group_id>/events/<int:event_id>/volunteers/remove', methods=['POST'])
@require_login
def remove_event_volunteer(group_id, event_id):
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()

    if not GroupService.can_user_manage_group(group_id, user_id, is_super_admin):
        return jsonify({'error': 'Permission denied'}), 403

    payload = request.get_json(silent=True) or {}
    member_id = payload.get('member_id')
    role_id = payload.get('role_id')

    try:
        member_id = int(member_id)
        role_id = int(role_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid assignment payload'}), 400

    try:
        GroupService.remove_event_volunteer(group_id, event_id, member_id, role_id)
        assignments = _build_event_assignment_payload(group_id, event_id)
        return jsonify({'success': True, 'assignments': assignments})
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except Exception as exc:
        current_app.logger.exception('Failed to remove volunteer: %s', exc)
        return jsonify({'error': 'Failed to remove volunteer'}), 500


def _initial_event_form_data(event=None, assigned_volunteer_requirements=None):
    """Prepare baseline form data for event create/edit flows"""
    if event:
        if isinstance(event, dict):
            event_datetime = event.get('datetime')
            name = event.get('name', '')
            town = event.get('town', '')
            event_type = event.get('event_type', '')
            description = event.get('description', '')
            max_participants = event.get('max_participants')
            visibility = event.get('visibility', 'public')
        else:
            event_datetime = getattr(event, 'datetime', None)
            name = getattr(event, 'name', '')
            town = getattr(event, 'town', '')
            event_type = getattr(event, 'event_type', '')
            description = getattr(event, 'description', '')
            max_participants = getattr(event, 'max_participants', '')
            visibility = getattr(event, 'visibility', 'public')

        date_value = event_datetime.strftime('%Y-%m-%d') if event_datetime else ''
        time_value = event_datetime.strftime('%H:%M') if event_datetime else ''
        base = {
            'name': name,
            'event_date': date_value,
            'event_time': time_value,
            'town': town,
            'event_type': event_type,
            'description': description or '',
            'max_participants': str(max_participants or ''),
            'visibility': visibility or 'public'
        }

        base['volunteer_requirements'] = _format_assigned_volunteer_requirements(assigned_volunteer_requirements)
        return base

    return {
        'name': '',
        'event_date': '',
        'event_time': '',
        'town': '',
        'event_type': '',
        'description': '',
        'max_participants': '',
        'visibility': 'public',
        'volunteer_requirements': []
    }


def _extract_event_form_submission():
    """Capture submitted values from the event form"""
    return {
        'name': (request.form.get('name') or '').strip(),
        'event_date': (request.form.get('event_date') or '').strip(),
        'event_time': (request.form.get('event_time') or '').strip(),
        'town': (request.form.get('town') or '').strip(),
        'event_type': (request.form.get('event_type') or '').strip(),
        'description': (request.form.get('description') or '').strip(),
        'max_participants': (request.form.get('max_participants') or '').strip(),
        'visibility': (request.form.get('visibility') or 'public').strip() or 'public',
        'volunteer_role_ids': request.form.getlist('volunteer_role_ids[]'),
        'volunteer_role_spots': request.form.getlist('volunteer_role_spots[]')
    }


def _validate_event_form(form_data):
    """Validate event form input and build payload for persistence"""
    errors = []

    name = form_data.get('name', '').strip()
    if not name:
        errors.append('Event name is required.')
    form_data['name'] = name

    town = form_data.get('town', '').strip()
    if not town:
        errors.append('Town is required.')
    form_data['town'] = town

    event_type = form_data.get('event_type', '').strip()
    if not event_type:
        errors.append('Event type is required.')
    form_data['event_type'] = event_type

    event_date = form_data.get('event_date', '').strip()
    event_time = form_data.get('event_time', '').strip()
    form_data['event_date'] = event_date
    form_data['event_time'] = event_time

    event_datetime = None
    if not event_date or not event_time:
        errors.append('Event date and time are required.')
    else:
        try:
            event_datetime = datetime.strptime(f"{event_date} {event_time}", '%Y-%m-%d %H:%M')
            if event_datetime <= datetime.now():
                errors.append('Events must be scheduled for a future date and time.')
        except ValueError:
            errors.append('Invalid date or time format. Please use the provided pickers.')

    max_participants_raw = form_data.get('max_participants', '').strip()
    form_data['max_participants'] = max_participants_raw
    try:
        max_participants = int(max_participants_raw)
        if max_participants <= 0:
            raise ValueError
    except ValueError:
        errors.append('Max participants must be a positive whole number.')
        max_participants = None

    visibility = form_data.get('visibility', 'public')
    if visibility not in {'public', 'private'}:
        errors.append('Invalid visibility option selected.')
    form_data['visibility'] = visibility if visibility in {'public', 'private'} else 'public'

    description = form_data.get('description', '').strip()
    form_data['description'] = description

    role_ids = form_data.pop('volunteer_role_ids', [])
    role_spots = form_data.pop('volunteer_role_spots', [])

    volunteer_requirements_display = []
    volunteer_requirements_payload = []
    seen_roles = set()

    for index, (role_id_raw, spots_raw) in enumerate(zip_longest(role_ids, role_spots, fillvalue='')):
        role_id_str = (role_id_raw or '').strip()
        spots_str = (spots_raw or '').strip()

        if not role_id_str and not spots_str:
            continue

        volunteer_requirements_display.append({
            'role_id': role_id_str,
            'spots': spots_str
        })

        if not role_id_str:
            errors.append(f'Volunteer requirement row {index + 1} is missing a role selection.')
            continue

        try:
            role_id = int(role_id_str)
        except (TypeError, ValueError):
            errors.append(f'Volunteer requirement row {index + 1} has an invalid role selection.')
            continue

        if role_id in seen_roles:
            errors.append('Each volunteer role can only be listed once per event.')
            continue

        seen_roles.add(role_id)

        try:
            spots_value = int(spots_str)
            if spots_value <= 0:
                raise ValueError
        except (TypeError, ValueError):
            errors.append(f'Volunteer requirement row {index + 1} requires a positive whole number of spots.')
            continue

        volunteer_requirements_payload.append({'role_id': role_id, 'spots': spots_value})

    form_data['volunteer_requirements'] = volunteer_requirements_display

    if errors or not event_datetime or max_participants is None:
        return errors, None

    payload = {
        'name': name,
        'event_datetime': event_datetime,
        'town': town,
        'event_type': event_type,
        'description': description or None,
        'max_participants': max_participants,
        'visibility': form_data['visibility'],
        'volunteer_requirements': volunteer_requirements_payload
    }

    return errors, payload


def _format_assigned_volunteer_requirements(assigned):
    if not assigned:
        return []

    formatted = []

    for item in assigned:
        if isinstance(item, dict):
            role_id = item.get('role_id') or item.get('task_id')
            spots = item.get('spots')
        else:
            role_id = getattr(item, 'role_id', None)
            if role_id is None:
                role_id = getattr(item, 'task_id', '')
            spots = getattr(item, 'spots', '')

        if role_id is None:
            continue

        formatted.append({
            'role_id': str(role_id),
            'spots': str(spots) if spots is not None else ''
        })

    return formatted


def _notify_event_participants(event_id, message, participants=None):
    """Log notifications for participants about event changes"""
    recipients = participants if participants is not None else GroupService.get_event_participants(event_id)
    notified = 0

    for participant in recipients:
        if isinstance(participant, dict):
            email = participant.get('email')
            user_ref = email or participant.get('id')
        else:
            email = getattr(participant, 'email', None)
            user_ref = email or getattr(participant, 'id', None)
        current_app.logger.info('Notify user %s about event %s: %s', user_ref, event_id, message)
        notified += 1

    return notified


@group_blueprint.route('/<int:group_id>/manage/members/<int:member_id>/role', methods=['POST'])
@require_login
def update_member_role(group_id, member_id):
    """Update a member's role in the group"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()
    
    if not GroupService.can_user_manage_group(group_id, user_id, is_super_admin):
        return jsonify({'error': 'Permission denied'}), 403
    
    payload = request.get_json(silent=True) or {}
    new_role = payload.get('role')

    allowed_roles = {'member', 'manager'}

    if new_role not in allowed_roles:
        return jsonify({'error': 'Invalid role'}), 400

    membership = GroupService.get_group_membership(group_id, member_id)
    if not membership or membership.get('member_status') != 'active':
        return jsonify({'error': 'Member not found'}), 404

    current_role = membership.get('group_role')

    if not is_super_admin and current_role == 'manager' and new_role != 'manager':
        return jsonify({'error': 'Only super admins can change manager roles'}), 403
    
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


@group_blueprint.route('/my-groups')
@require_login
def my_groups():
    """View user's groups"""
    user_id = auth_service.get_user_id()
    groups = GroupService.get_user_groups(user_id)
    managed_groups = GroupService.get_user_managed_groups(user_id)

    discovery_url = url_for('app.home_filter_events', filter_type='groups')
    create_group_url = None
    if auth_service.is_participant():
        encoded_id = encode_id(user_id)
        create_group_url = url_for('participant.create_group_applyform', encoded_participant_id=encoded_id)

    return render_template('group/my_groups.html', 
                         groups=groups,
                         managed_groups=managed_groups,
                         discovery_url=discovery_url,
                         create_group_url=create_group_url)


@group_blueprint.route('/participant-search')
@require_login
def participant_search():
    """Participant-specific search for groups and events"""
    user_id = auth_service.get_user_id()


    # Only allow participants to use this search
    if not auth_service.is_participant():
        flash('This search feature is for participants only', 'error')
        return redirect(_group_landing_url())

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
        flash(f'Error performing search: {str(e)}', 'error')
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


# Group Join Request Routes
@group_blueprint.route('/<int:group_id>/request-join')
@require_login
def request_join_form(group_id):
    """Show form to request joining a private group"""
    user_id = auth_service.get_user_id()
    next_url = (request.args.get('next') or '').strip()
    if next_url and not next_url.startswith('/'):
        next_url = ''

    try:
        can_join, join_action = GroupService.can_user_join_group_enhanced(group_id, user_id)
        if not can_join or join_action != 'request_access':
            flash('Cannot request to join this group', 'error')
            return redirect(url_for('groups.view_group', group_id=group_id))
    except Exception as e:
        flash('Error checking group permissions', 'error')
        return redirect(_group_landing_url())

    group = GroupService.get_group_by_id(group_id)
    if not group:
        flash('Group not found', 'error')
        return redirect(_group_landing_url())

    return render_template('group/join_request.html', group=group, next_url=next_url)

@group_blueprint.route('/<int:group_id>/cancel-join-request', methods=['POST'])
@require_login
def cancel_join_request(group_id):
   """
   Cancel pending join request for a private group
   """  
   user_id = auth_service.get_user_id()
    # get the URL parameter of the current page for redirection back
   search_term = request.args.get('search', '').strip()
   location_filter = request.args.get('location', '').strip()
   date_filter = request.args.get('date', '').strip()
   type_filter = request.args.get('type', '').strip()
   sort_by = request.args.get('sort', 'popularity').strip()
   try:
        
        result = GroupService.cancel_join_request(group_id, user_id)
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'error')
            
   except Exception as e:
        flash('Error cancelling join request', 'error')
    
   return redirect(url_for('groups.participant_search', group_id=group_id,        search=search_term,location=location_filter,date=date_filter, type=type_filter,
   sort=sort_by))

# 可选：添加查看待处理请求的路由 check if this one is used this is can delete only in the conter not used in the html page
@group_blueprint.route('/my-pending-requests')
@require_login
def my_pending_requests():
    """Show user's pending join requests"""
    user_id = auth_service.get_user_id()
    
    try:
        pending_requests = GroupService.get_user_pending_requests(user_id)
        return render_template('groups/my_pending_requests.html', 
                             pending_requests=pending_requests)
    except Exception as e:
        flash('Error loading your pending requests', 'error')
        return redirect(_group_landing_url())







@group_blueprint.route('/<int:group_id>/request-join', methods=['POST'])
@require_login
def submit_join_request(group_id):
    """Submit request to join private group"""
    user_id = auth_service.get_user_id()
    message = request.form.get('message', '').strip()
    next_url = (request.form.get('next') or '').strip()
    redirect_target = url_for('groups.view_group', group_id=group_id)
    if next_url.startswith('/'):
        redirect_target = next_url

    try:
        GroupService.request_to_join_group(user_id, group_id, message)
        flash('Your request to join has been submitted for review', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash('Error submitting request', 'error')

    return redirect(redirect_target)


@group_blueprint.route('/<int:group_id>/manage/join-requests')
@require_login
def manage_join_requests(group_id):
    """Manage pending join requests (for group managers)"""
    user_id = auth_service.get_user_id()
    is_super_admin = auth_service.is_super_admin()

    if not GroupService.can_user_manage_group(group_id, user_id, is_super_admin):
        flash('Permission denied', 'error')
        return redirect(url_for('groups.view_group', group_id=group_id))

    try:
        group = GroupService.get_group_by_id(group_id)
        if not group:
            flash('Group not found', 'error')
            return redirect(_group_landing_url())

        requests = GroupService.get_pending_join_requests(group_id)

        return render_template('group/manage_join_requests.html',
                             requests=requests, group=group)
    except Exception as e:
        flash(f'Error loading join requests: {str(e)}', 'error')
        return redirect(url_for('groups.manage_group', group_id=group_id))


@group_blueprint.route('/join-requests/<int:request_id>/approve', methods=['POST'])
@require_login
def approve_join_request(request_id):
    """Approve a join request"""
    manager_id = auth_service.get_user_id()

    try:
        GroupService.process_join_request(request_id, 'approve', manager_id)
        flash('Join request approved successfully and participant has been notified', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Error processing request: {str(e)}', 'error')

    # Get the group_id from the request to redirect back
    try:
        request_data = GroupService.get_join_request_by_id(request_id)
        if request_data:
            return redirect(url_for('groups.manage_join_requests', group_id=request_data['group_id']))
    except Exception as e:
        flash(f'Redirect error: {str(e)}', 'warning')

    return redirect(_group_landing_url())


@group_blueprint.route('/join-requests/<int:request_id>/reject', methods=['POST'])
@require_login
def reject_join_request(request_id):
    """Reject a join request"""
    manager_id = auth_service.get_user_id()
    rejection_reason = request.form.get('rejection_reason', '').strip()

    try:
        GroupService.process_join_request(request_id, 'reject', manager_id, rejection_reason)
        flash('Join request rejected and participant has been notified', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash('Error processing request', 'error')

    # Get the group_id from the request to redirect back
    try:
        request_data = GroupService.get_join_request_by_id(request_id)
        if request_data:
            return redirect(url_for('groups.manage_join_requests', group_id=request_data['group_id']))
    except Exception as e:
        flash(f'Redirect error: {str(e)}', 'warning')

    return redirect(_group_landing_url())