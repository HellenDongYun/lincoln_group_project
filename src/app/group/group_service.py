from collections import defaultdict
from datetime import datetime

from src.app.common.db.cursor import get_cursor
from src.app.group.group_repository import GroupRepository
from src.app.event.event import Event
from src.app.user.user import (
    CommunityGroup,
    GroupMembership,
    GroupApplication,
    GroupVisibility,
    GroupStatus,
)


class GroupService:

    CHALLENGE_STATUS_CHOICES = (
        {
            'value': 'draft',
            'label': 'Draft (hidden)',
            'description': 'Keep editing without showing the challenge to members.'
        },
        {
            'value': 'published',
            'label': 'Published (visible)',
            'description': 'Make the challenge live for group members.'
        },
        {
            'value': 'archived',
            'label': 'Archived (read-only)',
            'description': 'Preserve results without allowing new progress.'
        }
    )

    CHALLENGE_TARGET_METRICS = (
        {'value': 'events_attended', 'label': 'Events attended'},
        {'value': 'distance_km', 'label': 'Distance (km)'},
        {'value': 'volunteer_hours', 'label': 'Volunteer hours'},
        {'value': 'photos_submitted', 'label': 'Photos submitted'},
        {'value': 'elevation_gain_meters', 'label': 'Elevation gain (m)'},
        {'value': 'custom', 'label': 'Custom metric'}
    )

    CHALLENGE_STATUS_SET = {choice['value'] for choice in CHALLENGE_STATUS_CHOICES}
    
    @staticmethod
    def get_all_groups(visibility_filter=None, town_filter=None, page=1, per_page=10):
        """Get paginated list of groups"""
        offset = (page - 1) * per_page
        
        with get_cursor() as cursor:
            groups = GroupRepository.get_all_groups(
                cursor, visibility_filter, town_filter, per_page, offset
            )
            
            # Get total count for pagination
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM Community_Groups g 
                WHERE (%s IS NULL OR g.visibility = %s) 
                AND (%s IS NULL OR g.town = %s)
            """, (visibility_filter, visibility_filter, town_filter, town_filter))
            
            total_count = cursor.fetchone()['total']
            total_pages = (total_count + per_page - 1) // per_page
            
            return {
                'groups': groups,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'total_count': total_count
            }

    @staticmethod
    def get_group_by_id(group_id):
        """Get a specific group with its details"""
        with get_cursor() as cursor:
            return GroupRepository.get_group_by_id(cursor, group_id)

    @staticmethod
    def create_group(name, description, town, visibility, created_by):
        """Create a new group"""
        with get_cursor() as cursor:
            group_id = GroupRepository.create_group(
                cursor, name, description, town, visibility, created_by
            )
            # Add creator as manager
            GroupRepository.add_group_member(cursor, group_id, created_by, 'manager')
            return group_id

    @staticmethod
    def get_user_groups(user_id):
        """Get all groups a user belongs to"""
        with get_cursor() as cursor:
            return GroupRepository.get_user_groups(cursor, user_id)

    @staticmethod
    def get_group_members(group_id):
        """Get all members of a group"""
        with get_cursor() as cursor:
            return GroupRepository.get_group_members(cursor, group_id)

    @staticmethod
    def get_group_membership(group_id, user_id):
        """Get a member's current role and status within a group"""
        with get_cursor() as cursor:
            return GroupRepository.get_group_membership(cursor, group_id, user_id)

    @staticmethod
    def add_member_to_group(group_id, user_id, role='member'):
        """Add a user to a group"""
        with get_cursor() as cursor:
            return GroupRepository.add_group_member(cursor, group_id, user_id, role)

    @staticmethod
    def update_member_role(group_id, user_id, new_role):
        """Update a member's role in a group"""
        with get_cursor() as cursor:
            return GroupRepository.update_member_role(cursor, group_id, user_id, new_role)

    @staticmethod
    def remove_member_from_group(group_id, user_id):
        """Remove a member from a group"""
        with get_cursor() as cursor:
            return GroupRepository.remove_group_member(cursor, group_id, user_id)

    @staticmethod
    def is_group_manager(group_id, user_id):
        """Check if user is a manager of the group"""
        with get_cursor() as cursor:
            return GroupRepository.is_group_manager(cursor, group_id, user_id)

    @staticmethod
    def is_group_member(group_id, user_id):
        """Check if user is a member of the group"""
        with get_cursor() as cursor:
            return GroupRepository.is_group_member(cursor, group_id, user_id)

    @staticmethod
    def can_user_manage_group(group_id, user_id, is_super_admin=False):
        """Check if user can manage the group (super admin or group manager)"""
        if is_super_admin:
            return True
        return GroupService.is_group_manager(group_id, user_id)

    @staticmethod
    def can_user_join_group(group_id, user_id, is_super_admin=False):
        """Check if user can join a group"""
        with get_cursor() as cursor:
            group = GroupRepository.get_group_by_id(cursor, group_id)
            if not group:
                return False

            # Can't join if already a member
            if GroupRepository.is_group_member(cursor, group_id, user_id):
                return False

            visibility = str(group.get('visibility') or '').strip().lower()

            # Public groups are open to join
            if visibility == 'public':
                return True

            # Super admins can bypass visibility restrictions
            if is_super_admin:
                return True

            # Private or unknown visibility require manual approval
            return False

    # Group Applications
    @staticmethod
    def create_group_application(applicant_id, proposed_name, proposed_description, 
                               proposed_town, visibility):
        """Create a new group application"""
        with get_cursor() as cursor:
            return GroupRepository.create_group_application(
                cursor, applicant_id, proposed_name, proposed_description,
                proposed_town, visibility
            )

    @staticmethod
    def get_pending_applications():
        """Get all pending group applications for super admin review"""
        with get_cursor() as cursor:
            return GroupRepository.get_pending_applications(cursor)

    @staticmethod
    def get_application_by_id(application_id):
        """Get a specific group application"""
        with get_cursor() as cursor:
            return GroupRepository.get_application_by_id(cursor, application_id)

    @staticmethod
    def approve_group_application(application_id, decision_by):
        """Approve a group application and create the group"""
        with get_cursor() as cursor:
            application = GroupRepository.get_application_by_id(cursor, application_id)
            if not application or application['status'] != 'pending':
                raise ValueError("Application not found or not pending")

            # Update application status
            GroupRepository.update_application_status(cursor, application_id, 'approved', decision_by)
            
            # Create the group
            group_id = GroupRepository.create_group(
                cursor, 
                application['proposed_name'],
                application['proposed_description'],
                application['proposed_town'],
                application['visibility'],
                decision_by  # Super admin creates it
            )
            
            # Add applicant as manager
            GroupRepository.add_group_member(cursor, group_id, application['applicant_id'], 'manager')
            
            return group_id

    @staticmethod
    def reject_group_application(application_id, decision_by):
        """Reject a group application"""
        with get_cursor() as cursor:
            return GroupRepository.update_application_status(cursor, application_id, 'rejected', decision_by)

    @staticmethod
    def get_public_groups_for_discovery(town_filter=None, search_term=None):
        """Get public groups for discovery page"""
        with get_cursor() as cursor:
            return GroupRepository.get_public_groups_for_discovery(cursor, town_filter, search_term)

    @staticmethod
    def get_user_managed_groups(user_id):
        """Get groups where user is a manager"""
        with get_cursor() as cursor:
            groups = GroupRepository.get_user_groups(cursor, user_id)
            return [group for group in groups if group['group_role'] == 'manager']

    @staticmethod
    def get_group_events(group_id, include_past=False, limit=None, *, current_user_id=None, user_is_member=False):
        """Get events created for a group, enriched with registration context"""
        with get_cursor() as cursor:
            rows = GroupRepository.get_group_events(cursor, group_id, include_past, limit)
            events = []

            for row in rows:
                event = Event(**row)

                # Calculate current registrations and available spaces
                registrations = GroupRepository.count_event_participants(cursor, event.id)
                event.current_registrations = registrations
                if event.max_participants:
                    event.available_spaces = max(event.max_participants - registrations, 0)
                else:
                    event.available_spaces = None

                # Participant registration context
                event.is_registered = False
                event.registration_status = None
                event.can_register = False
                event.registration_blocked_reason = None

                if current_user_id:
                    record = GroupRepository.get_event_participant_record(cursor, event.id, current_user_id)
                    if record:
                        event.registration_status = record.get('status')
                        event.is_registered = record.get('status') == 'registered'

                # Volunteer opportunities context
                requirement_rows = GroupRepository.get_event_volunteer_requirements(cursor, event.id)
                assignment_rows = GroupRepository.get_event_volunteer_assignments(cursor, event.id)

                assignments_by_role = defaultdict(list)
                current_user_role_ids = set()
                for assignment in assignment_rows:
                    role_id = assignment.get('role_id')
                    if role_id is None:
                        continue
                    assignments_by_role[role_id].append(assignment)
                    if current_user_id and assignment.get('user_id') == current_user_id:
                        current_user_role_ids.add(role_id)

                volunteer_roles = []
                total_assigned = 0
                total_required = 0
                finite_required = True
                total_available = 0
                user_has_event_role = bool(current_user_role_ids)

                volunteer_blocked_reason = None
                if event.is_registered:
                    volunteer_blocked_reason = "You're already registered for this event. Cancel your registration before volunteering."

                for requirement in requirement_rows:
                    role_id = requirement.get('role_id')
                    role_name = requirement.get('name')
                    role_description = requirement.get('description')
                    spots_raw = requirement.get('spots')

                    required_spots = None
                    if spots_raw is not None:
                        try:
                            required_spots = int(spots_raw)
                        except (TypeError, ValueError):
                            required_spots = None

                    assigned_count = len(assignments_by_role.get(role_id, []))
                    total_assigned += assigned_count

                    if required_spots is None:
                        finite_required = False
                    else:
                        total_required += required_spots

                    available_spots = None
                    if required_spots is not None:
                        available_spots = max(required_spots - assigned_count, 0)
                        total_available += available_spots

                    is_assigned = role_id in current_user_role_ids
                    has_capacity = available_spots is None or available_spots > 0

                    volunteer_roles.append({
                        'id': role_id,
                        'name': role_name,
                        'description': role_description,
                        'required_spots': required_spots,
                        'assigned_count': assigned_count,
                        'available_spots': available_spots,
                        'is_assigned': is_assigned,
                        'can_volunteer': bool(user_is_member) and not is_assigned and not user_has_event_role and not event.is_registered and has_capacity
                    })

                event.volunteer_roles = volunteer_roles
                event.has_volunteer_roles = len(volunteer_roles) > 0
                event.volunteer_assigned = total_assigned
                if finite_required:
                    event.volunteer_required = total_required
                    event.volunteer_available = total_available
                else:
                    event.volunteer_required = None
                    event.volunteer_available = None
                event.user_is_volunteer = user_has_event_role
                event.user_volunteer_role_ids = list(current_user_role_ids)
                event.volunteer_blocked_reason = volunteer_blocked_reason

                if user_is_member and not event.is_registered:
                    has_capacity = (
                        event.available_spaces is None or event.available_spaces > 0
                    )
                    if has_capacity and not user_has_event_role:
                        event.can_register = True
                    elif user_has_event_role:
                        event.registration_blocked_reason = "You've already signed up to volunteer for this event."

                if event.is_registered and not event.user_is_volunteer:
                    event.registration_blocked_reason = event.registration_blocked_reason or "You're already registered for this event."

                events.append(event)

            return events

    @staticmethod
    def get_group_challenges(group_id, include_archived=True):
        """Return challenges for the given group"""
        with get_cursor() as cursor:
            rows = GroupRepository.get_group_challenges(cursor, group_id, include_archived)

        challenges = []
        target_metric_lookup = {
            option['value']: option.get('label', option['value'])
            for option in GroupService.get_challenge_target_metrics()
        }
        status_lookup = {
            option['value']: option.get('label', option['value'])
            for option in GroupService.get_challenge_status_choices()
        }

        for row in rows:
            challenge = dict(row)
            challenge['verification_required'] = bool(challenge.get('verification_required'))

            # Normalize numeric fields
            try:
                challenge['target_value'] = int(challenge.get('target_value'))
            except (TypeError, ValueError):
                challenge['target_value'] = None

            try:
                timeframe = challenge.get('timeframe_days')
                challenge['timeframe_days'] = int(timeframe) if timeframe is not None else None
            except (TypeError, ValueError):
                challenge['timeframe_days'] = None

            metric_value = challenge.get('target_metric')
            challenge['target_metric_label'] = target_metric_lookup.get(metric_value, metric_value)

            status_value = challenge.get('status')
            challenge['status_label'] = status_lookup.get(status_value, status_value)

            challenges.append(challenge)

        return challenges

    @classmethod
    def get_challenge_target_metrics(cls):
        return cls.CHALLENGE_TARGET_METRICS

    @classmethod
    def get_challenge_status_choices(cls):
        return cls.CHALLENGE_STATUS_CHOICES

    @staticmethod
    def get_group_challenge_options(group_id=None):
        with get_cursor() as cursor:
            achievements = GroupRepository.list_achievements(cursor)
            reward_labels = GroupRepository.list_reward_label_options(cursor)

        formatted_achievements = []
        for achievement in achievements:
            item = dict(achievement)
            points = item.get('points_reward')
            if points is not None:
                try:
                    item['points_reward'] = int(points)
                except (TypeError, ValueError):
                    item['points_reward'] = points
            formatted_achievements.append(item)

        return {
            'target_metrics': GroupService.get_challenge_target_metrics(),
            'status_choices': GroupService.get_challenge_status_choices(),
            'achievements': formatted_achievements,
            'reward_badge_labels': reward_labels.get('badges', []),
            'reward_trophy_labels': reward_labels.get('trophies', [])
        }

    @classmethod
    def validate_challenge_form(cls, form_data):
        """Validate challenge form input and return sanitised payload"""
        errors = []

        name = (form_data.get('name') or '').strip()
        if not name:
            errors.append('Challenge name is required.')

        description = (form_data.get('description') or '').strip()
        description_value = description or None

        target_metric = (form_data.get('target_metric') or '').strip()
        if not target_metric:
            errors.append('Target metric is required.')

        target_value_raw = (form_data.get('target_value') or '').strip()
        target_value = None
        if not target_value_raw:
            errors.append('Target value is required.')
        else:
            try:
                target_value = int(target_value_raw)
                if target_value <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append('Target value must be a positive whole number.')

        timeframe_raw = (form_data.get('timeframe_days') or '').strip()
        timeframe_days = None
        if timeframe_raw:
            try:
                timeframe_days = int(timeframe_raw)
                if timeframe_days <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append('Timeframe must be a positive whole number if provided.')

        achievement_raw = (form_data.get('achievement_id') or '').strip()
        achievement_id = None
        if achievement_raw:
            try:
                achievement_id = int(achievement_raw)
                if achievement_id <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append('Achievement selection is invalid.')
                achievement_id = None

        reward_badge_label = (form_data.get('reward_badge_label') or '').strip() or None
        reward_trophy_label = (form_data.get('reward_trophy_label') or '').strip() or None

        verification_required = str(form_data.get('verification_required')).lower() in {'1', 'true', 'on', 'yes'}

        status = (form_data.get('status') or 'draft').strip().lower()
        if status not in cls.CHALLENGE_STATUS_SET:
            errors.append('Invalid challenge status selected.')
            status = 'draft'

        payload = {
            'name': name,
            'description': description_value,
            'target_metric': target_metric,
            'target_value': target_value,
            'timeframe_days': timeframe_days,
            'achievement_id': achievement_id,
            'reward_badge_label': reward_badge_label,
            'reward_trophy_label': reward_trophy_label,
            'verification_required': verification_required,
            'status': status
        }

        return errors, payload

    @staticmethod
    def create_group_challenge(group_id, created_by, payload):
        """Persist a new group challenge"""
        published_at = datetime.utcnow() if payload['status'] == 'published' else None
        with get_cursor() as cursor:
            try:
                challenge_id = GroupRepository.create_group_challenge(cursor, group_id, created_by, payload, published_at)
            except Exception:
                raise
        return challenge_id

    @staticmethod
    def update_group_challenge(group_id, challenge_id, payload):
        """Update an existing challenge"""
        with get_cursor() as cursor:
            existing = GroupRepository.get_group_challenge(cursor, group_id, challenge_id)
            if not existing:
                raise ValueError('Challenge not found.')

            published_at = existing.get('published_at')
            if payload['status'] == 'published' and existing.get('status') != 'published':
                published_at = datetime.utcnow()
            if payload['status'] != 'published':
                published_at = None

            updated = GroupRepository.update_group_challenge(cursor, group_id, challenge_id, payload, published_at)
            if updated == 0:
                raise ValueError('Challenge update failed.')

    @staticmethod
    def delete_group_challenge(group_id, challenge_id):
        with get_cursor() as cursor:
            existing = GroupRepository.get_group_challenge(cursor, group_id, challenge_id)
            if not existing:
                raise ValueError('Challenge not found.')

            deleted = GroupRepository.delete_group_challenge(cursor, group_id, challenge_id)
            if deleted == 0:
                raise ValueError('Unable to delete challenge.')

    @staticmethod
    def get_group_event(group_id, event_id):
        """Get a single event for a group"""
        with get_cursor() as cursor:
            row = GroupRepository.get_group_event(cursor, group_id, event_id)
            return Event(**row) if row else None

    @staticmethod
    def create_group_event(group_id, created_by, **event_data):
        """Create a new event under a group"""
        with get_cursor() as cursor:
            event_payload = event_data.copy()
            volunteer_requirements = event_payload.pop('volunteer_requirements', [])

            event_id = GroupRepository.create_group_event(cursor, group_id, created_by, **event_payload)

            if volunteer_requirements:
                GroupRepository.replace_event_volunteer_requirements(cursor, event_id, volunteer_requirements)

            return event_id

    @staticmethod
    def update_group_event(group_id, event_id, **event_data):
        """Update an existing group event"""
        with get_cursor() as cursor:
            update_payload = event_data.copy()
            volunteer_requirements = update_payload.pop('volunteer_requirements', None)

            updated = GroupRepository.update_group_event(cursor, group_id, event_id, **update_payload)

            if volunteer_requirements is not None:
                GroupRepository.replace_event_volunteer_requirements(cursor, event_id, volunteer_requirements)

            return updated

    @staticmethod
    def cancel_group_event(group_id, event_id):
        """Cancel (delete) an event belonging to a group"""
        with get_cursor() as cursor:
            return GroupRepository.delete_group_event(cursor, group_id, event_id)

    @staticmethod
    def get_event_participants(event_id):
        """Return participants registered for an event"""
        with get_cursor() as cursor:
            return GroupRepository.get_event_participants(cursor, event_id)

    @staticmethod
    def get_all_volunteer_roles():
        """Return the global volunteer role catalogue"""
        with get_cursor() as cursor:
            return GroupRepository.get_all_volunteer_roles(cursor)

    @staticmethod
    def get_event_volunteer_requirements(event_id):
        """Return volunteer requirements configured for an event"""
        with get_cursor() as cursor:
            return GroupRepository.get_event_volunteer_requirements(cursor, event_id)

    @staticmethod
    def get_event_volunteer_assignments(event_id):
        """Return volunteer assignments for an event"""
        with get_cursor() as cursor:
            return GroupRepository.get_event_volunteer_assignments(cursor, event_id)

    @staticmethod
    def get_event_assignment_snapshot(group_id, event_id):
        """Collect participants and volunteer assignment details for a group event"""
        with get_cursor() as cursor:
            event = GroupRepository.get_group_event(cursor, group_id, event_id)
            if not event:
                raise ValueError('Event not found')
            if isinstance(event, dict):
                event = Event(**event)

            participants = GroupRepository.get_event_participants(cursor, event_id)
            volunteer_requirements = GroupRepository.get_event_volunteer_requirements(cursor, event_id)
            volunteer_assignments = GroupRepository.get_event_volunteer_assignments(cursor, event_id)

        return {
            'event': event,
            'participants': participants,
            'volunteer_requirements': volunteer_requirements,
            'volunteer_assignments': volunteer_assignments
        }

    @staticmethod
    def assign_event_participant(group_id, event_id, member_id):
        """Assign a group member as a participant for the event"""
        with get_cursor() as cursor:
            event = GroupRepository.get_group_event(cursor, group_id, event_id)
            if not event:
                raise ValueError('Event not found')

            membership = GroupRepository.get_group_membership(cursor, group_id, member_id)
            if not membership or membership.get('member_status') != 'active':
                raise ValueError('Member not found in group')

            max_participants = event.get('max_participants') if isinstance(event, dict) else getattr(event, 'max_participants', None)
            if max_participants is not None:
                try:
                    max_participants = int(max_participants)
                except (TypeError, ValueError):
                    max_participants = None
            if max_participants is not None:
                current_count = GroupRepository.count_event_participants(cursor, event_id)
                if current_count >= max_participants:
                    raise ValueError('Event is at capacity')

            record = GroupRepository.get_event_participant_record(cursor, event_id, member_id)
            if record and record.get('status') == 'registered':
                raise ValueError('Member is already registered for this event')

            GroupRepository.add_event_participant(cursor, event_id, member_id)
            return True

    @staticmethod
    def remove_event_participant(group_id, event_id, member_id):
        """Remove a participant assignment from the event"""
        with get_cursor() as cursor:
            event = GroupRepository.get_group_event(cursor, group_id, event_id)
            if not event:
                raise ValueError('Event not found')

            record = GroupRepository.get_event_participant_record(cursor, event_id, member_id)
            if not record or record.get('status') != 'registered':
                raise ValueError('Member is not registered for this event')

            GroupRepository.remove_event_participant(cursor, event_id, member_id)
            return True

    @staticmethod
    def assign_event_volunteer(group_id, event_id, member_id, role_id):
        """Assign a group member to a volunteer role for the event"""
        with get_cursor() as cursor:
            event = GroupRepository.get_group_event(cursor, group_id, event_id)
            if not event:
                raise ValueError('Event not found')

            membership = GroupRepository.get_group_membership(cursor, group_id, member_id)
            if not membership or membership.get('member_status') != 'active':
                raise ValueError('Member not found in group')

            participant_record = GroupRepository.get_event_participant_record(cursor, event_id, member_id)
            if participant_record and participant_record.get('status') == 'registered':
                raise ValueError("You're already registered for this event. Cancel your registration before volunteering.")

            if GroupRepository.is_user_volunteer_for_event(cursor, event_id, member_id):
                raise ValueError("You've already signed up to volunteer for this event.")

            requirement = GroupRepository.get_event_volunteer_requirement(cursor, event_id, role_id)
            if not requirement:
                raise ValueError('Volunteer role not configured for this event')

            if GroupRepository.is_user_volunteer_for_role(cursor, event_id, role_id, member_id):
                raise ValueError("You've already signed up to volunteer for this event.")

            spots = requirement.get('spots') if isinstance(requirement, dict) else getattr(requirement, 'spots', None)
            if spots is not None:
                try:
                    spots = int(spots)
                except (TypeError, ValueError):
                    spots = None
            if spots is not None:
                assigned_count = GroupRepository.count_event_volunteer_assignments(cursor, event_id, role_id)
                if assigned_count >= spots:
                    raise ValueError('No remaining spots for this role')

            GroupRepository.assign_event_volunteer(cursor, event_id, role_id, member_id)
            return True

    @staticmethod
    def remove_event_volunteer(group_id, event_id, member_id, role_id):
        """Remove a volunteer assignment from the event"""
        with get_cursor() as cursor:
            event = GroupRepository.get_group_event(cursor, group_id, event_id)
            if not event:
                raise ValueError('Event not found')

            if not GroupRepository.is_user_volunteer_for_role(cursor, event_id, role_id, member_id):
                raise ValueError('Member is not assigned to this volunteer role')

            GroupRepository.remove_event_volunteer(cursor, event_id, role_id, member_id)
            return True

    @staticmethod
    def get_manager_dashboard_snapshot(group_id, include_past_events=False):
        """Return aggregated analytics for the group manager dashboard"""

        def _format_duration(seconds):
            if seconds is None:
                return None
            seconds = int(round(seconds))
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            if hours:
                return f"{hours:d}:{minutes:02d}:{secs:02d}"
            return f"{minutes:d}:{secs:02d}"

        with get_cursor() as cursor:
            membership_counts = GroupRepository.get_group_membership_counts(cursor, group_id) or {}
            event_rows = GroupRepository.get_group_event_metrics(cursor, group_id, include_past_events)
            result_rows = GroupRepository.get_group_result_details(cursor, group_id)
            activity_rows = GroupRepository.get_group_member_activity(cursor, group_id)
            volunteer_assignment_rows = GroupRepository.get_group_volunteer_assignments(cursor, group_id)
            duration_rows = GroupRepository.get_event_average_durations(cursor, group_id)

        counts = {
            'total_members': membership_counts.get('total_members', 0) or 0,
            'participants': membership_counts.get('participants', 0) or 0,
            'managers': membership_counts.get('managers', 0) or 0,
            'volunteers': 0
        }

        # Event metrics with volunteer coverage and no-show calculations
        events = []
        now = datetime.now()

        for row in event_rows:
            event_datetime = row.get('datetime')
            registrations = row.get('registrations') or 0
            attendance_raw = row.get('attendance') or 0
            no_shows_raw = max(registrations - attendance_raw, 0)
            is_past = bool(event_datetime and event_datetime < now)
            attendance = attendance_raw if is_past else None
            no_shows = no_shows_raw if is_past else None
            volunteer_needed = row.get('volunteer_needed') or 0
            volunteer_assigned = row.get('volunteer_assigned') or 0
            if volunteer_needed > 0:
                volunteer_coverage = min(volunteer_assigned / volunteer_needed * 100, 100)
            else:
                volunteer_coverage = 100 if volunteer_assigned > 0 else 0

            events.append({
                'id': row['id'],
                'name': row['name'],
                'datetime': row['datetime'],
                'registrations': registrations,
                'attendance': attendance,
                'attendance_display': attendance if attendance is not None else '–',
                'no_shows': no_shows,
                'no_shows_display': no_shows if no_shows is not None else '–',
                'volunteer_needed': volunteer_needed,
                'volunteer_assigned': volunteer_assigned,
                'volunteer_gap': max(volunteer_needed - volunteer_assigned, 0),
                'volunteer_coverage_percent': round(volunteer_coverage, 1),
                'is_past': is_past
            })

        total_events = len(events)

        # Performance metrics derived from results
        total_results = len(result_rows)
        total_seconds_accum = 0
        personal_best_map = {}
        group_record = None

        for row in result_rows:
            total_seconds = row['total_seconds'] or 0
            total_seconds_accum += total_seconds

            entry = personal_best_map.get(row['user_id'])
            if entry is None or total_seconds < entry['seconds']:
                personal_best_map[row['user_id']] = {
                    'user_id': row['user_id'],
                    'name': f"{row['first_name']} {row['last_name']}",
                    'seconds': total_seconds,
                    'formatted': _format_duration(total_seconds),
                    'event_name': row['event_name'],
                    'event_datetime': row['event_datetime']
                }

            if group_record is None or total_seconds < group_record['seconds']:
                group_record = {
                    'user_id': row['user_id'],
                    'name': f"{row['first_name']} {row['last_name']}",
                    'seconds': total_seconds,
                    'formatted': _format_duration(total_seconds),
                    'event_name': row['event_name'],
                    'event_datetime': row['event_datetime']
                }

        personal_bests = sorted(personal_best_map.values(), key=lambda item: item['seconds'])
        average_event_time = total_seconds_accum / total_results if total_results else None

        # Engagement metrics
        most_active = []
        for row in activity_rows:
            most_active.append({
                'user_id': row['user_id'],
                'name': f"{row['first_name']} {row['last_name']}",
                'registrations': row.get('registrations') or 0,
                'attended_events': row.get('attended_events') or 0
            })
        most_active.sort(key=lambda item: (item['attended_events'], item['registrations']), reverse=True)

        duration_lookup = {row['event_id']: row['avg_duration_seconds'] or 0 for row in duration_rows}
        default_event_seconds = 5400  # 1.5 hours default when results are not available

        volunteer_summary = defaultdict(lambda: {'assignments': 0, 'seconds': 0, 'name': ''})
        for row in volunteer_assignment_rows:
            user_id = row['user_id']
            volunteer_summary[user_id]['assignments'] += 1
            volunteer_summary[user_id]['name'] = f"{row['first_name']} {row['last_name']}"
            event_seconds = duration_lookup.get(row['event_id']) or default_event_seconds
            volunteer_summary[user_id]['seconds'] += event_seconds

        volunteer_participation = []
        for user_id, stats in volunteer_summary.items():
            hours = float(stats['seconds']) / 3600
            hours = round(hours, 2)
            volunteer_participation.append({
                'user_id': user_id,
                'name': stats['name'],
                'assignments': stats['assignments'],
                'hours': hours
            })
        volunteer_participation.sort(key=lambda item: (item['assignments'], item['hours']), reverse=True)

        counts['volunteers'] = len(volunteer_participation)

        return {
            'membership_counts': counts,
            'events': {
                'total': total_events,
                'items': events
            },
            'performance': {
                'average_time_seconds': average_event_time,
                'average_time_display': _format_duration(average_event_time) if average_event_time else None,
                'personal_bests': personal_bests,
                'group_record': group_record
            },
            'engagement': {
                'most_active': most_active,
                'volunteer_participation': volunteer_participation,
                'volunteer_hours_total': round(sum(item['hours'] for item in volunteer_participation), 2)
            }
        }

    @staticmethod
    def update_group_settings(group_id, visibility, status):
        """Update group visibility and status"""
        with get_cursor() as cursor:
            return GroupRepository.update_group_settings(cursor, group_id, visibility, status)

    @staticmethod
    def search_for_participants(participant_id, search_term=None, location_filter=None,
                              date_filter=None, type_filter=None, sort_by='popularity'):
        """Get search results specifically for participants with join/register context"""
        with get_cursor() as cursor:
            results = GroupRepository.search_groups_and_events_for_participants(
                cursor, participant_id, search_term, location_filter,
                date_filter, type_filter
            )

            processed_results = []
            sort_key = (sort_by or 'popularity').strip().lower()

            for result in results:
                processed_result = dict(result)
                raw_events = processed_result.pop('events', None)
                events = []

                if raw_events:
                    events_iterable = raw_events
                else:
                    events_blob = processed_result.pop('events_data', '')
                    if events_blob:
                        events_iterable = events_blob.split(';;')
                    else:
                        events_iterable = []

                for event_entry in events_iterable:
                    if isinstance(event_entry, dict):
                        event_data = event_entry
                    else:
                        event_string = (event_entry or '').strip()
                        if not event_string:
                            continue
                        parts = event_string.split('|')
                        if len(parts) < 7:
                            continue
                        event_data = {
                            'id': parts[0].strip(),
                            'name': parts[1].strip(),
                            'description': parts[2].strip() if parts[2] != 'None' else '',
                            'datetime': parts[3].strip(),
                            'event_type': parts[4].strip(),
                            'max_participants': parts[5].strip(),
                            'registered_count': parts[6].strip()
                        }

                    event = {
                        'id': event_data.get('id'),
                        'name': (event_data.get('name') or '').strip(),
                        'description': (event_data.get('description') or ''),
                        'event_type': (event_data.get('event_type') or '').strip() or None,
                        'town': event_data.get('town'),
                        'registered_count': int(event_data.get('registered_count') or 0)
                    }

                    raw_datetime = event_data.get('datetime')
                    dt_obj = None
                    if isinstance(raw_datetime, datetime):
                        dt_obj = raw_datetime
                    elif isinstance(raw_datetime, str) and raw_datetime:
                        try:
                            dt_obj = datetime.strptime(raw_datetime, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            dt_obj = None

                    if dt_obj:
                        event['formatted_datetime'] = dt_obj.strftime('%Y-%m-%d %H:%M')
                        event['datetime_sort'] = dt_obj
                    else:
                        event['formatted_datetime'] = raw_datetime or 'TBD'
                        event['datetime_sort'] = None

                    max_participants = event_data.get('max_participants')
                    try:
                        max_participants = int(max_participants) if max_participants is not None else None
                    except (TypeError, ValueError):
                        max_participants = None

                    if max_participants is not None:
                        event['max_participants'] = max_participants
                        registered = event['registered_count']
                        event['available_spaces'] = max(max_participants - registered, 0)

                    events.append(event)

                events.sort(key=lambda item: (item.get('datetime_sort') or datetime.max, item['name'].lower()))

                processed_result['events'] = events
                processed_result['upcoming_events'] = len(events)
                processed_result['can_join'] = GroupService._can_participant_join_group(processed_result)
                processed_result['join_action'] = GroupService._get_group_join_action(processed_result)

                processed_results.append(processed_result)

            if sort_key == 'alphabetical':
                processed_results.sort(key=lambda item: item['group_name'].lower())
            elif sort_key == 'date':
                def first_event_datetime(group_item):
                    if not group_item['events']:
                        return datetime.max
                    return min((evt.get('datetime_sort') or datetime.max) for evt in group_item['events'])

                processed_results.sort(key=lambda item: (first_event_datetime(item), item['group_name'].lower()))
            else:
                processed_results.sort(key=lambda item: (-int(item.get('popularity_score', 0)), item['group_name'].lower()))

            for item in processed_results:
                for event in item['events']:
                    event.pop('datetime_sort', None)

            return processed_results

    @staticmethod
    def get_participant_search_filter_options():
        """Get filter options for participant search (locations, event types, etc.)"""
        with get_cursor() as cursor:
            return GroupRepository.get_participant_search_filter_options(cursor)

    @staticmethod
    def _can_participant_join_group(group_result):
        """Helper to determine if participant can join a group"""
        # Already a member
        if group_result.get('participant_group_role'):
            return False

        # Can join if group is public
        if group_result.get('visibility') == 'public':
            return True

        # Private groups require application
        return group_result.get('visibility') == 'private'

    @staticmethod
    def _get_group_join_action(group_result):
        """Helper to get the appropriate join action for a group"""
        if group_result.get('participant_group_role') == 'manager':
            return 'manage'
        elif group_result.get('participant_group_role') == 'member':
            return 'member'
        elif group_result.get('pending_join_request') == 'pending':
            return 'request_pending'   # Already has pending request
        elif group_result.get('visibility') == 'public':
            return 'join_immediately'  # Public groups = immediate join
        elif group_result.get('visibility') == 'private':
            return 'request_access'    # Private groups = request required
        else:
            return 'closed'

    @staticmethod
    def _can_participant_register_for_event(event_result):
        """Helper to determine if participant can register for an event"""
        # Already registered
        if event_result.get('participant_event_status') == 'registered':
            return False

        # Check if event is full
        if event_result.get('max_participants'):
            registered = event_result.get('registered_participants', 0)
            if registered >= event_result['max_participants']:
                return False

        # Can register if event is in the future
        return True

    @staticmethod
    def _get_event_register_action(event_result):
        """Helper to get the appropriate register action for an event"""
        if event_result.get('participant_event_status') == 'registered':
            return 'registered'
        elif event_result.get('max_participants'):
            registered = event_result.get('registered_participants', 0)
            if registered >= event_result['max_participants']:
                return 'full'

        return 'register'

    # Group Join Request Methods
    @staticmethod
    def get_join_action_for_group(group, user_id):
        """Determine what join action is available for user"""
        with get_cursor() as cursor:
            # Check if already a member
            if GroupRepository.is_group_member(cursor, group['id'], user_id):
                # Check if manager
                if GroupRepository.is_group_manager(cursor, group['id'], user_id):
                    return 'manage'
                else:
                    return 'member'

            # Check if has pending request
            existing_request = GroupRepository.check_existing_join_request(cursor, user_id, group['id'])
            if existing_request:
                return 'request_pending'

            # Determine action based on visibility
            if group['visibility'] == 'public':
                return 'join_immediately'
            elif group['visibility'] == 'private':
                return 'request_access'
            else:
                return 'closed'

    @staticmethod
    def request_to_join_group(user_id, group_id, message=None):
        """Submit request to join private group"""
        with get_cursor() as cursor:
            # Validate group exists and is private
            group = GroupRepository.get_group_by_id(cursor, group_id)
            if not group:
                raise ValueError("Group not found")

            if group['visibility'] != 'private':
                raise ValueError("Only private groups require join requests")

            # Check if already a member
            if GroupRepository.is_group_member(cursor, group_id, user_id):
                raise ValueError("Already a member of this group")

            # Check for existing pending request
            existing_request = GroupRepository.check_existing_join_request(cursor, user_id, group_id)
            if existing_request:
                raise ValueError("You already have a pending request for this group")

            # Create the join request
            return GroupRepository.create_join_request(cursor, user_id, group_id, message)

    @staticmethod
    def get_pending_join_requests(group_id):
        """Get pending join requests for group managers"""
        with get_cursor() as cursor:
            return GroupRepository.get_pending_join_requests(cursor, group_id)

    @staticmethod
    def get_join_request_by_id(request_id):
        """Get specific join request details"""
        with get_cursor() as cursor:
            return GroupRepository.get_join_request_by_id(cursor, request_id)

    @staticmethod
    def process_join_request(request_id, action, manager_id):
        """Approve or reject join request"""
        with get_cursor() as cursor:
            # Get request details
            request = GroupRepository.get_join_request_by_id(cursor, request_id)
            if not request or request['status'] != 'pending':
                raise ValueError("Request not found or already processed")

            # Validate manager permissions
            if not GroupRepository.is_group_manager(cursor, request['group_id'], manager_id):
                raise ValueError("Only group managers can process join requests")

            if action == 'approve':
                # Update request status
                GroupRepository.update_join_request_status(cursor, request_id, 'approved', manager_id)
                # Add user to group as member
                GroupRepository.add_group_member(cursor, request['group_id'], request['user_id'], 'member')
                return True
            elif action == 'reject':
                # Update request status
                GroupRepository.update_join_request_status(cursor, request_id, 'rejected', manager_id)
                return True
            else:
                raise ValueError("Invalid action. Must be 'approve' or 'reject'")

    @staticmethod
    def can_user_join_group_enhanced(group_id, user_id):
        """Enhanced version that returns join action details"""
        with get_cursor() as cursor:
            group = GroupRepository.get_group_by_id(cursor, group_id)
            if not group:
                return False, "Group not found"

            action = GroupService.get_join_action_for_group(group, user_id)

            if action in ['join_immediately', 'request_access']:
                return True, action
            else:
                return False, action

    @staticmethod
    def user_has_group_memberships(user_id):
        """Check if user has any group memberships (can volunteer)"""
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM Group_Memberships gm
                WHERE gm.user_id = %s AND gm.member_status = 'active'
            """, (user_id,))

            result = cursor.fetchone()
            return result['count'] > 0 if result else False
