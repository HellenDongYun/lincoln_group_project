from src.app.common.db.repository import Repository
from src.app.common.db.cursor import get_cursor
from src.app.user.user import CommunityGroup, GroupMembership, GroupApplication, GroupVisibility, GroupStatus, GroupRole


class GroupRepository(Repository):
    
    @staticmethod
    def get_all_groups(cursor, visibility_filter=None, town_filter=None, limit=None, offset=0):
        """Get all groups with optional filtering"""
        query = """
            SELECT g.id, g.name, g.description, g.town, g.visibility,
                   g.status, g.created_by,
                   COUNT(gm.user_id) as member_count
            FROM Community_Groups g
            LEFT JOIN Group_Memberships gm ON g.id = gm.group_id AND gm.member_status = 'active'
            WHERE 1=1
        """
        params = []
        
        if visibility_filter:
            query += " AND g.visibility = %s"
            params.append(visibility_filter)
            
        if town_filter:
            query += " AND g.town = %s"
            params.append(town_filter)
            
        query += " GROUP BY g.id, g.name, g.description, g.town, g.visibility, g.status, g.created_by"
        query += " ORDER BY g.name ASC"
        
        if limit:
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

        cursor.execute(query, tuple(params))
        return cursor.fetchall()

    @staticmethod
    def search_groups_and_events_for_participants(cursor, participant_id, search_term=None,
                                                location_filter=None, date_filter=None,
                                                type_filter=None, sort_by='popularity'):
        """Participant-specific search focusing on groups with their event information"""
        # Build search conditions
        search_conditions = ""
        params = [participant_id, participant_id]  # Used twice: once for participant_gm, once for pending_request

        if search_term and search_term.strip():
            search_pattern = f"%{search_term.strip()}%"
            search_conditions += " AND (g.name LIKE %s OR g.description LIKE %s)"
            params.extend([search_pattern, search_pattern])

        if location_filter and location_filter.strip():
            search_conditions += " AND g.town = %s"
            params.append(location_filter.strip())

        # Event-specific date filters
        event_date_filter = ""
        if date_filter and date_filter.strip():
            if date_filter.strip() == "next_2_weeks":
                event_date_filter = " AND e.datetime <= DATE_ADD(NOW(), INTERVAL 2 WEEK)"
            elif date_filter.strip() == "next_month":
                event_date_filter = " AND e.datetime <= DATE_ADD(NOW(), INTERVAL 1 MONTH)"
            elif date_filter.strip() == "upcoming":
                event_date_filter = " AND e.datetime > NOW()"

        # Event type filter
        event_type_filter = ""
        if type_filter and type_filter.strip():
            event_type_filter = f" AND e.event_type = %s"
            params.append(type_filter.strip())

        # Single query to get groups with their event details
        query = f"""
            SELECT
                g.id as group_id, g.name as group_name, g.description as group_description,
                g.town, g.visibility,
                g.status as group_status,
                COUNT(DISTINCT gm.user_id) as member_count,
                COUNT(DISTINCT CASE WHEN e.datetime > NOW() THEN e.id END) as upcoming_events,

                -- Event information (JSON-like string with all events)
                GROUP_CONCAT(DISTINCT
                    CASE WHEN e.id IS NOT NULL AND e.datetime > NOW() {event_date_filter} {event_type_filter}
                    THEN CONCAT(e.id, '|', e.name, '|', e.description, '|', e.datetime, '|', e.event_type, '|',
                                COALESCE(e.max_participants, 0), '|',
                                COALESCE(event_participants.registered_count, 0))
                    END
                    SEPARATOR ';;'
                ) as events_data,

                CASE WHEN participant_gm.user_id IS NOT NULL THEN participant_gm.group_role
                     ELSE NULL END as participant_group_role,

                -- Check for pending join request
                CASE WHEN pending_request.id IS NOT NULL THEN 'pending'
                     ELSE NULL END as pending_join_request,

                'group' as result_type,
                (COUNT(DISTINCT gm.user_id) + COUNT(DISTINCT CASE WHEN e.datetime > NOW() THEN e.id END)) as popularity_score

            FROM Community_Groups g
            LEFT JOIN Group_Memberships gm ON g.id = gm.group_id AND gm.member_status = 'active'
            LEFT JOIN Events e ON g.id = e.group_id
            LEFT JOIN Group_Memberships participant_gm ON g.id = participant_gm.group_id
                     AND participant_gm.user_id = %s AND participant_gm.member_status = 'active'
            LEFT JOIN Group_Join_Requests pending_request ON g.id = pending_request.group_id
                     AND pending_request.user_id = %s AND pending_request.status = 'pending'
            LEFT JOIN (
                SELECT event_id, COUNT(*) as registered_count
                FROM Event_Participants
                WHERE status = 'registered'
                GROUP BY event_id
            ) event_participants ON e.id = event_participants.event_id

            WHERE g.status = 'active' {search_conditions}
            GROUP BY g.id
        """

        # Add sorting
        if sort_by == 'popularity':
            query += " ORDER BY popularity_score DESC, g.name ASC"
        elif sort_by == 'alphabetical':
            query += " ORDER BY g.name ASC"
        elif sort_by == 'date':
            query += " ORDER BY upcoming_events DESC, g.name ASC"
        else:
            query += " ORDER BY popularity_score DESC, g.name ASC"

        cursor.execute(query, tuple(params))
        return cursor.fetchall()

    @staticmethod
    def get_participant_search_filter_options(cursor):
        """Get filter options for participant search dropdowns"""
        # Get unique locations from both groups and events
        cursor.execute("""
            SELECT DISTINCT town FROM (
                SELECT DISTINCT g.town
                FROM Community_Groups g
                WHERE g.town IS NOT NULL AND g.town != '' AND g.status = 'active'
                UNION
                SELECT DISTINCT e.town
                FROM Events e
                JOIN Community_Groups g ON e.group_id = g.id
                WHERE e.town IS NOT NULL AND e.town != '' AND e.datetime > NOW() AND g.status = 'active'
            ) AS locations
            ORDER BY town
        """)
        locations = [row['town'] for row in cursor.fetchall()]

        # Get unique event types from future events
        cursor.execute("""
            SELECT DISTINCT e.event_type
            FROM Events e
            JOIN Community_Groups g ON e.group_id = g.id
            WHERE e.event_type IS NOT NULL AND e.event_type != ''
            AND e.datetime > NOW() AND g.status = 'active'
            ORDER BY e.event_type
        """)
        event_types = [row['event_type'] for row in cursor.fetchall()]

        return {
            'locations': locations,
            'event_types': event_types
        }

    @staticmethod
    def get_group_by_id(cursor, group_id):
        """Get a specific group by ID"""
        cursor.execute("""
            SELECT g.id, g.name, g.description, g.town, g.visibility,
                   g.status, g.created_by,
                   u.first_name, u.last_name,
                   COUNT(gm.user_id) as member_count
            FROM Community_Groups g
            JOIN Users u ON g.created_by = u.id
            LEFT JOIN Group_Memberships gm ON g.id = gm.group_id AND gm.member_status = 'active'
            WHERE g.id = %s
            GROUP BY g.id
        """, (group_id,))
        return cursor.fetchone()

    @staticmethod
    def create_group(cursor, name, description, town, visibility, created_by):
        """Create a new group"""
        cursor.execute("""
            INSERT INTO Community_Groups (name, description, town, visibility, status, created_by)
            VALUES (%s, %s, %s, %s, 'active', %s)
        """, (name, description, town, visibility, created_by))
        return cursor.lastrowid

    @staticmethod
    def get_user_groups(cursor, user_id):
        """Get all groups a user is a member of"""
        cursor.execute("""
         SELECT g.id, g.name, g.description, g.town, g.visibility,
             g.status,
             gm.group_role,
             gm.member_status
            FROM Community_Groups g
            JOIN Group_Memberships gm ON g.id = gm.group_id
            WHERE gm.user_id = %s AND gm.member_status = 'active'
            ORDER BY g.name ASC
        """, (user_id,))
        return cursor.fetchall()

    @staticmethod
    def get_group_members(cursor, group_id):
        """Get all members of a group"""
        cursor.execute("""
         SELECT u.id, u.first_name, u.last_name, u.email, u.town,
             gm.group_role,
             gm.member_status
            FROM Users u
            JOIN Group_Memberships gm ON u.id = gm.user_id
         WHERE gm.group_id = %s AND gm.member_status = 'active'
         ORDER BY group_role DESC, u.first_name ASC
        """, (group_id,))
        return cursor.fetchall()

    @staticmethod
    def get_group_membership(cursor, group_id, user_id):
        """Get a specific member's role and status in a group"""
        cursor.execute("""
         SELECT group_role,
             member_status
            FROM Group_Memberships
            WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id))
        return cursor.fetchone()

    @staticmethod
    def add_group_member(cursor, group_id, user_id, group_role='member'):
        """Add a user to a group"""
        cursor.execute("""
            INSERT INTO Group_Memberships (group_id, user_id, group_role, member_status)
            VALUES (%s, %s, %s, 'active')
            ON DUPLICATE KEY UPDATE member_status = 'active', group_role = %s
        """, (group_id, user_id, group_role, group_role))
        return cursor.rowcount

    @staticmethod
    def update_member_role(cursor, group_id, user_id, new_role):
        """Update a member's role in a group"""
        cursor.execute("""
            UPDATE Group_Memberships 
            SET group_role = %s 
            WHERE group_id = %s AND user_id = %s
        """, (new_role, group_id, user_id))
        return cursor.rowcount

    @staticmethod
    def remove_group_member(cursor, group_id, user_id):
        """Remove a user from a group"""
        cursor.execute("""
            UPDATE Group_Memberships 
            SET member_status = 'inactive' 
            WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id))
        return cursor.rowcount

    @staticmethod
    def is_group_manager(cursor, group_id, user_id):
        """Check if a user is a manager of a specific group"""
        cursor.execute("""
            SELECT 1 FROM Group_Memberships 
            WHERE group_id = %s AND user_id = %s 
            AND group_role = 'manager' AND member_status = 'active'
        """, (group_id, user_id))
        return cursor.fetchone() is not None

    @staticmethod
    def is_group_member(cursor, group_id, user_id):
        """Check if a user is a member of a specific group"""
        cursor.execute("""
            SELECT 1 FROM Group_Memberships 
            WHERE group_id = %s AND user_id = %s AND member_status = 'active'
        """, (group_id, user_id))
        return cursor.fetchone() is not None

    @staticmethod
    def update_group_settings(cursor, group_id, visibility, status):
        """Update visibility and status of a group"""
        cursor.execute("""
            UPDATE Community_Groups
            SET visibility = %s, status = %s
            WHERE id = %s
        """, (visibility, status, group_id))
        return cursor.rowcount

    @staticmethod
    def get_group_events(cursor, group_id, include_past=False, limit=None):
        """Fetch events associated with a group"""
        query = """
            SELECT e.id, e.group_id, e.datetime, e.town, e.name, e.event_type,
                   e.description, e.max_participants, e.visibility, e.created_by
            FROM Events e
            WHERE e.group_id = %s
        """
        params = [group_id]

        if not include_past:
            query += " AND e.datetime >= NOW()"

        query += " ORDER BY e.datetime ASC"

        if limit is not None:
            query += " LIMIT %s"
            params.append(limit)

        cursor.execute(query, params)
        return cursor.fetchall()

    @staticmethod
    def get_group_event(cursor, group_id, event_id):
        """Fetch a single event and ensure it belongs to the group"""
        cursor.execute("""
            SELECT e.id, e.group_id, e.datetime, e.town, e.name, e.event_type,
                   e.description, e.max_participants, e.visibility, e.created_by
            FROM Events e
            WHERE e.id = %s AND e.group_id = %s
        """, (event_id, group_id))
        return cursor.fetchone()

    @staticmethod
    def create_group_event(cursor, group_id, created_by, *, name, event_datetime,
                           town, event_type, description, max_participants, visibility):
        """Create a new event for a group"""
        cursor.execute("""
            INSERT INTO Events (group_id, datetime, town, name, event_type, description,
                                max_participants, visibility, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (group_id, event_datetime, town, name, event_type, description,
               max_participants, visibility, created_by))
        return cursor.lastrowid

    @staticmethod
    def update_group_event(cursor, group_id, event_id, *, name, event_datetime,
                           town, event_type, description, max_participants, visibility):
        """Update an existing group event"""
        cursor.execute("""
            UPDATE Events
            SET datetime = %s,
                town = %s,
                name = %s,
                event_type = %s,
                description = %s,
                max_participants = %s,
                visibility = %s
            WHERE id = %s AND group_id = %s
        """, (event_datetime, town, name, event_type, description,
               max_participants, visibility, event_id, group_id))
        return cursor.rowcount

    @staticmethod
    def delete_group_event(cursor, group_id, event_id):
        """Delete/cancel an event belonging to the group"""
        cursor.execute("""
            DELETE FROM Events
            WHERE id = %s AND group_id = %s
        """, (event_id, group_id))
        return cursor.rowcount

    @staticmethod
    def get_event_participants(cursor, event_id):
        """Get active participants registered for an event"""
        cursor.execute("""
            SELECT u.id, u.first_name, u.last_name, u.email
            FROM Event_Participants ep
            JOIN Users u ON ep.user_id = u.id
            WHERE ep.event_id = %s AND ep.status = 'registered'
        """, (event_id,))
        return cursor.fetchall()

    @staticmethod
    def count_event_participants(cursor, event_id):
        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM Event_Participants
            WHERE event_id = %s AND status = 'registered'
        """, (event_id,))
        row = cursor.fetchone()
        return row['count'] if row else 0

    @staticmethod
    def get_event_participant_record(cursor, event_id, user_id):
        cursor.execute("""
            SELECT status
            FROM Event_Participants
            WHERE event_id = %s AND user_id = %s
        """, (event_id, user_id))
        return cursor.fetchone()

    @staticmethod
    def add_event_participant(cursor, event_id, user_id):
        """Register a group member as an event participant"""
        cursor.execute("""
            INSERT INTO Event_Participants (event_id, user_id, status)
            VALUES (%s, %s, 'registered')
            ON DUPLICATE KEY UPDATE status = 'registered'
        """, (event_id, user_id))
        return cursor.rowcount

    @staticmethod
    def remove_event_participant(cursor, event_id, user_id):
        """Mark a participant's registration as cancelled"""
        cursor.execute("""
            UPDATE Event_Participants
            SET status = 'cancelled'
            WHERE event_id = %s AND user_id = %s
        """, (event_id, user_id))
        return cursor.rowcount

    @staticmethod
    def get_all_volunteer_roles(cursor):
        """Return the catalogue of available volunteer roles"""
        cursor.execute("""
            SELECT id, name, description
            FROM Volunteer_Tasks
            ORDER BY name ASC
        """)
        return cursor.fetchall()

    @staticmethod
    def get_event_volunteer_requirements(cursor, event_id):
        """Return volunteer requirements configured for an event"""
        cursor.execute("""
            SELECT etv.task_id AS role_id,
                   vt.name,
                   vt.description,
                   etv.spots
            FROM Event_Task_Vacancies etv
            JOIN Volunteer_Tasks vt ON etv.task_id = vt.id
            WHERE etv.event_id = %s
            ORDER BY vt.name ASC
        """, (event_id,))
        return cursor.fetchall()

    @staticmethod
    def get_event_volunteer_requirement(cursor, event_id, role_id):
        cursor.execute("""
            SELECT task_id AS role_id, spots
            FROM Event_Task_Vacancies
            WHERE event_id = %s AND task_id = %s
        """, (event_id, role_id))
        return cursor.fetchone()

    @staticmethod
    def get_event_volunteer_assignments(cursor, event_id):
        cursor.execute("""
            SELECT
                eta.user_id,
                u.first_name,
                u.last_name,
                u.email,
                eta.task_id AS role_id,
                vt.name AS role_name
            FROM Event_Task_Assignments eta
            JOIN Users u ON u.id = eta.user_id
            JOIN Volunteer_Tasks vt ON vt.id = eta.task_id
            WHERE eta.event_id = %s
            ORDER BY vt.name ASC, u.first_name ASC, u.last_name ASC
        """, (event_id,))
        return cursor.fetchall()

    @staticmethod
    def count_event_volunteer_assignments(cursor, event_id, role_id):
        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM Event_Task_Assignments
            WHERE event_id = %s AND task_id = %s
        """, (event_id, role_id))
        row = cursor.fetchone()
        return row['count'] if row else 0

    @staticmethod
    def is_user_volunteer_for_role(cursor, event_id, role_id, user_id):
        cursor.execute("""
            SELECT 1
            FROM Event_Task_Assignments
            WHERE event_id = %s AND task_id = %s AND user_id = %s
        """, (event_id, role_id, user_id))
        return cursor.fetchone() is not None

    @staticmethod
    def is_user_volunteer_for_event(cursor, event_id, user_id):
        cursor.execute("""
            SELECT 1
            FROM Event_Task_Assignments
            WHERE event_id = %s AND user_id = %s
            LIMIT 1
        """, (event_id, user_id))
        return cursor.fetchone() is not None

    @staticmethod
    def assign_event_volunteer(cursor, event_id, role_id, user_id):
        cursor.execute("""
            INSERT INTO Event_Task_Assignments (event_id, task_id, user_id)
            VALUES (%s, %s, %s)
        """, (event_id, role_id, user_id))
        return cursor.rowcount

    @staticmethod
    def remove_event_volunteer(cursor, event_id, role_id, user_id):
        cursor.execute("""
            DELETE FROM Event_Task_Assignments
            WHERE event_id = %s AND task_id = %s AND user_id = %s
        """, (event_id, role_id, user_id))
        return cursor.rowcount

    @staticmethod
    def replace_event_volunteer_requirements(cursor, event_id, requirements):
        """Persist volunteer requirements for an event, replacing existing rows"""
        cursor.execute("DELETE FROM Event_Task_Vacancies WHERE event_id = %s", (event_id,))

        if not requirements:
            return

        values = [(event_id, req['role_id'], req['spots']) for req in requirements]
        cursor.executemany(
            """
            INSERT INTO Event_Task_Vacancies (event_id, task_id, spots)
            VALUES (%s, %s, %s)
            """,
            values
        )

    # Group Applications
    @staticmethod
    def create_group_application(cursor, applicant_id, proposed_name, proposed_description, 
                               proposed_town, visibility):
        """Create a new group application"""
        cursor.execute("""
            INSERT INTO Group_Applications 
            (applicant_id, proposed_name, proposed_description, proposed_town, visibility, status)
            VALUES (%s, %s, %s, %s, %s, 'pending')
        """, (applicant_id, proposed_name, proposed_description, proposed_town, visibility))
        return cursor.lastrowid

    # Analytics helpers
    @staticmethod
    def get_group_membership_counts(cursor, group_id):
        cursor.execute("""
            SELECT
                COUNT(*) AS total_members,
                SUM(CASE WHEN gm.group_role = 'member' THEN 1 ELSE 0 END) AS participants,
                SUM(CASE WHEN gm.group_role = 'manager' THEN 1 ELSE 0 END) AS managers
            FROM Group_Memberships gm
            WHERE gm.group_id = %s AND gm.member_status = 'active'
        """, (group_id,))
        return cursor.fetchone()

    @staticmethod
    def get_group_event_metrics(cursor, group_id, include_past=False):
        query = """
            SELECT
                e.id,
                e.name,
                e.datetime,
                COALESCE(reg.registrations, 0) AS registrations,
                COALESCE(att.attendance, 0) AS attendance,
                COALESCE(vac.required_spots, 0) AS volunteer_needed,
                COALESCE(assign.assigned_volunteers, 0) AS volunteer_assigned
            FROM Events e
            LEFT JOIN (
                SELECT ep.event_id, COUNT(DISTINCT CASE WHEN ep.status = 'registered' THEN ep.user_id END) AS registrations
                FROM Event_Participants ep
                GROUP BY ep.event_id
            ) reg ON reg.event_id = e.id
            LEFT JOIN (
                SELECT er.event_id, COUNT(DISTINCT er.user_id) AS attendance
                FROM Event_Results er
                GROUP BY er.event_id
            ) att ON att.event_id = e.id
            LEFT JOIN (
                SELECT etv.event_id, SUM(etv.spots) AS required_spots
                FROM Event_Task_Vacancies etv
                GROUP BY etv.event_id
            ) vac ON vac.event_id = e.id
            LEFT JOIN (
                SELECT eta.event_id, COUNT(DISTINCT eta.user_id) AS assigned_volunteers
                FROM Event_Task_Assignments eta
                GROUP BY eta.event_id
            ) assign ON assign.event_id = e.id
            WHERE e.group_id = %s
        """

        params = [group_id]
        if not include_past:
            query += "\n              AND e.datetime >= NOW()"

        query += "\n            ORDER BY e.datetime DESC"

        cursor.execute(query, params)
        return cursor.fetchall()

    @staticmethod
    def get_group_result_details(cursor, group_id):
        cursor.execute("""
            SELECT
                er.event_id,
                er.user_id,
                er.total_seconds,
                e.name AS event_name,
                e.datetime AS event_datetime,
                u.first_name,
                u.last_name
            FROM Event_Results er
            JOIN Events e ON e.id = er.event_id
            JOIN Users u ON u.id = er.user_id
            WHERE e.group_id = %s
        """, (group_id,))
        return cursor.fetchall()

    @staticmethod
    def get_group_member_activity(cursor, group_id):
        cursor.execute("""
            SELECT
                u.id AS user_id,
                u.first_name,
                u.last_name,
                COALESCE(reg.registrations, 0) AS registrations,
                COALESCE(att.attended_events, 0) AS attended_events
            FROM Group_Memberships gm
            JOIN Users u ON u.id = gm.user_id
            LEFT JOIN (
                SELECT ep.user_id, e.group_id, COUNT(DISTINCT ep.event_id) AS registrations
                FROM Event_Participants ep
                JOIN Events e ON e.id = ep.event_id
                WHERE ep.status = 'registered'
                GROUP BY ep.user_id, e.group_id
            ) reg ON reg.user_id = gm.user_id AND reg.group_id = gm.group_id
            LEFT JOIN (
                SELECT er.user_id, e.group_id, COUNT(DISTINCT er.event_id) AS attended_events
                FROM Event_Results er
                JOIN Events e ON e.id = er.event_id
                GROUP BY er.user_id, e.group_id
            ) att ON att.user_id = gm.user_id AND att.group_id = gm.group_id
            WHERE gm.group_id = %s AND gm.member_status = 'active'
        """, (group_id,))
        return cursor.fetchall()

    @staticmethod
    def get_group_volunteer_assignments(cursor, group_id):
        cursor.execute("""
            SELECT
                eta.user_id,
                u.first_name,
                u.last_name,
                eta.event_id
            FROM Event_Task_Assignments eta
            JOIN Events e ON e.id = eta.event_id
            JOIN Users u ON u.id = eta.user_id
            WHERE e.group_id = %s
        """, (group_id,))
        return cursor.fetchall()

    @staticmethod
    def get_event_average_durations(cursor, group_id):
        cursor.execute("""
            SELECT
                e.id AS event_id,
                AVG(er.total_seconds) AS avg_duration_seconds
            FROM Events e
            JOIN Event_Results er ON er.event_id = e.id
            WHERE e.group_id = %s
            GROUP BY e.id
        """, (group_id,))
        return cursor.fetchall()

    @staticmethod
    def get_pending_applications(cursor):
        """Get all pending group applications"""
        cursor.execute("""
            SELECT ga.id, ga.applicant_id, ga.proposed_name, ga.proposed_description, 
                   ga.proposed_town, ga.visibility, ga.status,
                   u.first_name, u.last_name, u.email
            FROM Group_Applications ga
            JOIN Users u ON ga.applicant_id = u.id
            WHERE ga.status = 'pending'
            ORDER BY ga.id ASC
        """)
        return cursor.fetchall()

    @staticmethod
    def get_application_by_id(cursor, application_id):
        """Get a specific group application"""
        cursor.execute("""
            SELECT ga.*, u.first_name, u.last_name, u.email
            FROM Group_Applications ga
            JOIN Users u ON ga.applicant_id = u.id
            WHERE ga.id = %s
        """, (application_id,))
        return cursor.fetchone()

    @staticmethod
    def update_application_status(cursor, application_id, status, decision_by):
        """Update the status of a group application"""
        cursor.execute("""
            UPDATE Group_Applications 
            SET status = %s, decision_by = %s
            WHERE id = %s
        """, (status, decision_by, application_id))
        return cursor.rowcount

    @staticmethod
    def get_public_groups_for_discovery(cursor, town_filter=None, search_term=None):
        """Get public groups for discovery by visitors and participants"""
        query = """
         SELECT g.id, g.name, g.description, g.town, g.visibility,
                   COUNT(gm.user_id) as member_count,
                   COUNT(CASE WHEN e.datetime > NOW() THEN 1 END) as upcoming_events
            FROM Community_Groups g
            LEFT JOIN Group_Memberships gm ON g.id = gm.group_id AND gm.member_status = 'active'
            LEFT JOIN Events e ON g.id = e.group_id
            WHERE g.visibility = 'public' AND g.status = 'active'
        """
        params = []
        
        if town_filter:
            query += " AND g.town = %s"
            params.append(town_filter)
            
        if search_term:
            query += " AND (g.name LIKE %s OR g.description LIKE %s)"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern])
            
        query += """
            GROUP BY g.id, g.name, g.description, g.town
            ORDER BY upcoming_events DESC, member_count DESC, g.name ASC
        """

        cursor.execute(query, params)
        return cursor.fetchall()

    # Group Join Requests
    @staticmethod
    def create_join_request(cursor, user_id, group_id, message=None):
        """Create a request to join a private group"""
        # First, delete any existing records for this user-group combination
        # This prevents duplicate key errors from the unique constraint
        cursor.execute("""
            DELETE FROM Group_Join_Requests
            WHERE user_id = %s AND group_id = %s
        """, (user_id, group_id))

        # Now create the new pending request
        cursor.execute("""
            INSERT INTO Group_Join_Requests (user_id, group_id, message, status)
            VALUES (%s, %s, %s, 'pending')
        """, (user_id, group_id, message))
        return cursor.lastrowid

    @staticmethod
    def get_pending_join_requests(cursor, group_id):
        """Get pending join requests for a group"""
        cursor.execute("""
            SELECT gjr.id, gjr.user_id, gjr.message, gjr.created_at,
                   u.first_name, u.last_name, u.email
            FROM Group_Join_Requests gjr
            JOIN Users u ON gjr.user_id = u.id
            WHERE gjr.group_id = %s AND gjr.status = 'pending'
            ORDER BY gjr.created_at ASC
        """, (group_id,))
        return cursor.fetchall()

    @staticmethod
    def update_join_request_status(cursor, request_id, status, reviewed_by, rejection_reason=None):
        """Approve or reject a join request"""
        # First get the request details to know user_id and group_id
        cursor.execute("""
            SELECT user_id, group_id FROM Group_Join_Requests WHERE id = %s
        """, (request_id,))
        request_info = cursor.fetchone()

        if not request_info:
            return 0

        user_id = request_info['user_id']
        group_id = request_info['group_id']

        # Delete any existing records with the same user-group-status combination
        # to avoid unique constraint violations
        cursor.execute("""
            DELETE FROM Group_Join_Requests
            WHERE user_id = %s AND group_id = %s AND status = %s AND id != %s
        """, (user_id, group_id, status, request_id))

        # Now update the current request status
        cursor.execute("""
            UPDATE Group_Join_Requests
            SET status = %s, reviewed_by = %s, reviewed_at = NOW(), rejection_reason = %s
            WHERE id = %s
        """, (status, reviewed_by, rejection_reason, request_id))
        return cursor.rowcount

    @staticmethod
    def check_existing_join_request(cursor, user_id, group_id):
        """Check if user already has pending request"""
        cursor.execute("""
            SELECT id FROM Group_Join_Requests
            WHERE user_id = %s AND group_id = %s AND status = 'pending'
        """, (user_id, group_id))
        return cursor.fetchone()

    @staticmethod
    def get_join_request_by_id(cursor, request_id):
        """Get specific join request details"""
        cursor.execute("""
            SELECT gjr.*, u.first_name, u.last_name, u.email,
                   g.name as group_name
            FROM Group_Join_Requests gjr
            JOIN Users u ON gjr.user_id = u.id
            JOIN Community_Groups g ON gjr.group_id = g.id
            WHERE gjr.id = %s
        """, (request_id,))
        return cursor.fetchone()

    @staticmethod
    def create_notification(cursor, user_id, notification_type, reference_id, message):
        """Create a notification for a user"""
        cursor.execute("""
            INSERT INTO Notifications (user_id, type, reference_id, message)
            VALUES (%s, %s, %s, %s)
        """, (user_id, notification_type, reference_id, message))
        return cursor.lastrowid