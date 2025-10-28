from src.app.common.db.cursor import get_cursor
from src.app.common.db.repository import Repository
from datetime import timedelta

class ParticipantRepository(Repository):  
    def get_upcoming_events(self, participant_id):
        """Get all upcoming events that the participant is not already registered for"""
        sql = """
            SELECT 
                e.id as Event_ID,
                e.name as Event_Name,
                DATE(e.datetime) as Event_Date,
                TIME(e.datetime) as Event_Time,
                e.town as Event_Location,
                e.event_type as Event_Type,
                e.description as Event_Description,
                e.max_participants as Max_Participants,
                COALESCE(COUNT(ep.user_id), 0) as Current_Registrations,
                (e.max_participants - COALESCE(COUNT(ep.user_id), 0)) as Available_Spots
            FROM Events e
            LEFT JOIN Event_Participants ep ON e.id = ep.event_id AND ep.status = 'registered'
            WHERE DATE(e.datetime) >= CURDATE()
            AND e.id NOT IN (
                SELECT event_id 
                FROM Event_Participants 
                WHERE user_id = %s AND status = 'registered'
            )
            GROUP BY e.id, e.name, DATE(e.datetime), TIME(e.datetime), e.town, e.event_type, e.description, e.max_participants
            ORDER BY DATE(e.datetime) ASC, TIME(e.datetime) ASC
        """
        try:
            return self.fetchall(sql, (participant_id,))
        except Exception as e:
            print(f"Database error in get_upcoming_events: {e}")
            return []
    
    def get_my_registrations(self, participant_id):
        """Get events that the participant is registered for"""
        sql = """
            SELECT 
                e.id as Event_ID,
                e.name as Event_Name,
                DATE(e.datetime) as Event_Date,
                TIME(e.datetime) as Event_Time,
                e.town as Event_Location,
                e.event_type as Event_Type,
                e.description as Event_Description,
                ep.status as Registration_Status
            FROM Event_Participants ep
            JOIN Events e ON ep.event_id = e.id
            WHERE ep.user_id = %s
            AND ep.status = 'registered'
            AND DATE(e.datetime) >= CURDATE()
            ORDER BY DATE(e.datetime) ASC, TIME(e.datetime) ASC
        """
        try:
            return self.fetchall(sql, (participant_id,))
        except Exception as e:
            print(f"Database error in get_my_registrations: {e}")
            return []
    
    def get_my_race_results(self, participant_id):
        """Get participant's past race results"""
        sql = """
            SELECT 
                e.id AS Event_ID,
                e.name AS Event_Name,
                DATE(e.datetime) AS Event_Date,
                e.town AS Event_Location,
                e.event_type AS Event_Type,
                er.start_time AS Start_Time,
                er.end_time AS End_Time,
                SEC_TO_TIME(TIMESTAMPDIFF(SECOND, er.start_time, er.end_time)) AS Race_Time,
                TIMESTAMPDIFF(SECOND, er.start_time, er.end_time) AS Race_Time_Seconds,
                RANK() OVER (
                    PARTITION BY er.event_id
                    ORDER BY TIMESTAMPDIFF(SECOND, er.start_time, er.end_time)
                ) AS Position,
                (
                    SELECT COUNT(*)
                    FROM Event_Results er2
                    WHERE er2.event_id = er.event_id
                      AND er2.start_time IS NOT NULL
                      AND er2.end_time IS NOT NULL
                ) AS Total_Participants
            FROM Event_Results er
            JOIN Events e ON er.event_id = e.id
            WHERE er.user_id = %s
              AND DATE(e.datetime) < CURDATE()
              AND er.start_time IS NOT NULL
              AND er.end_time IS NOT NULL
            ORDER BY DATE(e.datetime) DESC
        """
        try:
            return self.fetchall(sql, (participant_id,))
        except Exception as e:
            print(f"Database error in get_my_race_results: {e}")
            return []
    
    def register_for_event(self, participant_id, event_id):
        """Register a participant for an event"""
        # First check if already registered (only active registrations)
        check_sql = """
            SELECT COUNT(*) as count 
            FROM Event_Participants 
            WHERE user_id = %s AND event_id = %s AND status = 'registered'
        """
        
        try:
            existing = self.fetchone(check_sql, (participant_id, event_id))
            if existing and existing['count'] > 0:
                return False  # Already registered
            
            # Check if event is full
            capacity_sql = """
                SELECT 
                    e.max_participants,
                    COUNT(ep.user_id) as current_registrations
                FROM Events e
                LEFT JOIN Event_Participants ep ON e.id = ep.event_id AND ep.status = 'registered'
                WHERE e.id = %s
                GROUP BY e.id, e.max_participants
            """
            
            capacity_check = self.fetchone(capacity_sql, (event_id,))
            if capacity_check:
                if capacity_check['current_registrations'] >= capacity_check['max_participants']:
                    return False  # Event is full
            
            # Register for the event
            # First check if there's a cancelled registration we can reactivate
            cancelled_check_sql = """
                SELECT COUNT(*) as count 
                FROM Event_Participants 
                WHERE user_id = %s AND event_id = %s AND status = 'cancelled'
            """
            
            cancelled_record = self.fetchone(cancelled_check_sql, (participant_id, event_id))
            
            if cancelled_record and cancelled_record['count'] > 0:
                # Reactivate cancelled registration
                reactivate_sql = """
                    UPDATE Event_Participants 
                    SET status = 'registered'
                    WHERE user_id = %s AND event_id = %s AND status = 'cancelled'
                """
                result = self.execute(reactivate_sql, (participant_id, event_id))
            else:
                # Create new registration
                register_sql = """
                    INSERT INTO Event_Participants (user_id, event_id, status)
                    VALUES (%s, %s, 'registered')
                """
                result = self.execute(register_sql, (participant_id, event_id))
            
            return result is not None
            
        except Exception as e:
            print(f"Database error in register_for_event: {e}")
            return False
    
    def cancel_registration(self, participant_id, event_id):
        """Cancel a participant's registration for an event"""
        try:
            # Check if the participant is registered for this event
            check_sql = """
                SELECT COUNT(*) as count 
                FROM Event_Participants 
                WHERE user_id = %s AND event_id = %s AND status = 'registered'
            """
            
            existing = self.fetchone(check_sql, (participant_id, event_id))
            if not existing or existing['count'] == 0:
                return False  # Not registered or already cancelled
            
            # Update the registration status to cancelled
            cancel_sql = """
                UPDATE Event_Participants 
                SET status = 'cancelled'
                WHERE user_id = %s AND event_id = %s
            """
            
            result = self.execute(cancel_sql, (participant_id, event_id))
            return result is not None
            
        except Exception as e:
            print(f"Database error in cancel_registration: {e}")
            return False
    
    
    def show_application(self, status, page, per_page, participant_id):
        """Show the applications for a participant"""
        query = '''
        SELECT
            ga.proposed_name AS name,
            ga.proposed_description AS description,
            ga.proposed_town AS town,
            ga.visibility,
            ga.status,
            ga.application_time,
            ga.id,
            reviewer.email,
            CONCAT(reviewer.first_name, ' ', reviewer.last_name) AS full_name
        FROM Group_Applications ga
        LEFT JOIN Users reviewer ON ga.decision_by = reviewer.id
        WHERE ga.applicant_id = %s
        '''
        params = [participant_id]

        if status != "all":
            query += " AND ga.status = %s"
            params.append(status)

        offset = (page - 1) * per_page
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        with get_cursor() as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            # Count total
            count_query = '''
            SELECT COUNT(*) AS total
            FROM Group_Applications ga
            WHERE ga.applicant_id = %s
            '''
            count_params = [participant_id]

            if status != "all":
                count_query += " AND ga.status = %s"
                count_params.append(status)

            cursor.execute(count_query, tuple(count_params))
            total = cursor.fetchone()["total"]
        return rows, total

    def create_group_application(
        self, participant_id, name, description, town, visibility
    ):
        with get_cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) AS count
                FROM Group_Applications
                WHERE proposed_name = %s
            """,
                (name,),
            )
            if cursor.fetchone()["count"] > 0:
                raise ValueError(
                    "Group name already exists. Please choose a different name."
                )

            cursor.execute(
                """
                INSERT INTO Group_Applications (
                    applicant_id,
                    proposed_name,
                    proposed_description,
                    proposed_town,
                    visibility
                ) VALUES (%s, %s, %s, %s, %s)
            """,
                (participant_id, name, description, town, visibility),
            )
            return cursor.lastrowid

    def get_application_by_id(self, participant_id, application_id):
        with get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM Group_Applications WHERE id = %s AND applicant_id = %s
            """,
                (application_id, participant_id),
            )
            return cursor.fetchone()

    def update_group_application(
        self, participant_id, application_id, name, town, visibility, description
    ):
        with get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE Group_Applications
                SET proposed_name = %s, proposed_town = %s, visibility = %s, proposed_description = %s
                WHERE id = %s AND applicant_id = %s
            """,
                (name, town, visibility, description, application_id, participant_id),
            )

    def delete_group_application(self, participant_id, application_id):
        with get_cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM Group_Applications WHERE id = %s AND applicant_id = %s
            """,
                (application_id, participant_id),
            )

    def get_achievements_for_user(self, participant_id):
        sql = """
            SELECT
                a.id,
                a.name,
                a.description,
                a.points_reward,
                ua.earned_at
            FROM Achievements a
            LEFT JOIN User_Achievements ua
                ON ua.achievement_id = a.id
                AND ua.user_id = %s
            ORDER BY
                ua.earned_at IS NULL,
                a.points_reward DESC,
                a.name ASC
        """

        achievements = self.fetchall(sql, (participant_id,))
        for achievement in achievements:
            achievement["earned"] = achievement.get("earned_at") is not None
        return achievements

    def get_challenges_for_user(self, participant_id):
        sql = """
            SELECT
                c.id,
                c.name,
                c.description,
                c.target_metric,
                c.target_value,
                c.timeframe_days,
                c.achievement_id_reward,
                a.name AS achievement_name,
                a.points_reward,
                ua.earned_at
            FROM Challenges c
            JOIN Achievements a ON c.achievement_id_reward = a.id
            LEFT JOIN User_Achievements ua
                ON ua.achievement_id = c.achievement_id_reward
                AND ua.user_id = %s
            ORDER BY
                ua.earned_at IS NULL,
                a.points_reward DESC,
                c.name ASC
        """

        challenges = self.fetchall(sql, (participant_id,))
        for challenge in challenges:
            # Earned if User_Achievements has a record OR progress meets/exceeds target
            target_value = challenge.get("target_value") or 0
            timeframe_days = challenge.get("timeframe_days")
            target_metric = challenge.get("target_metric")

            progress_count = self._compute_challenge_progress(
                participant_id, target_metric, timeframe_days
            )

            # Default earned state from DB
            earned_db = challenge.get("earned_at") is not None
            earned_progress = (
                progress_count is not None and target_value and int(progress_count) >= int(target_value)
            )

            challenge["earned"] = bool(earned_db or earned_progress)
            challenge["progress_count"] = progress_count
            challenge["remaining"] = (
                0 if earned_progress else (max(0, int(target_value) - int(progress_count)) if (progress_count is not None and target_value) else None)
            )
        return challenges

    def _compute_challenge_progress(self, participant_id, target_metric: str, timeframe_days: int | None):
        """Return current progress count for a given challenge metric.
        Applies timeframe_days when provided (uses event datetime or result start_time).
        Returns None if metric is unsupported.
        """
        if not target_metric:
            return None

        # Helper to build timeframe predicate
        timeframe_clause_er = ""
        timeframe_clause_e = ""
        timeframe_param = []
        if timeframe_days:
            timeframe_clause_er = " AND er.start_time >= DATE_SUB(NOW(), INTERVAL %s DAY)"
            timeframe_clause_e = " AND e.datetime >= DATE_SUB(NOW(), INTERVAL %s DAY)"
            timeframe_param = [timeframe_days]

        with get_cursor() as cursor:
            # Events attended (all-time or within timeframe)
            if target_metric == "events_attended":
                sql = (
                    "SELECT COUNT(DISTINCT er.event_id) AS cnt "
                    "FROM Event_Results er WHERE er.user_id = %s" + timeframe_clause_er
                )
                cursor.execute(sql, [participant_id] + timeframe_param)
                row = cursor.fetchone()
                return row.get("cnt") if row else 0

            # Events attended within recent window (uses timeframe_days)
            if target_metric == "events_attended_monthly":
                # Use timeframe_days if provided (e.g., 30), otherwise default 30
                days = timeframe_days if timeframe_days else 30
                sql = (
                    "SELECT COUNT(DISTINCT er.event_id) AS cnt "
                    "FROM Event_Results er WHERE er.user_id = %s AND er.start_time >= DATE_SUB(NOW(), INTERVAL %s DAY)"
                )
                cursor.execute(sql, (participant_id, days))
                row = cursor.fetchone()
                return row.get("cnt") if row else 0

            # Volunteer tasks (count of assignments)
            if target_metric == "volunteer_tasks":
                sql = (
                    "SELECT COUNT(DISTINCT CONCAT(eta.event_id, '_', eta.task_id)) AS cnt "
                    "FROM Event_Task_Assignments eta JOIN Events e ON eta.event_id = e.id "
                    "WHERE eta.user_id = %s" + timeframe_clause_e
                )
                cursor.execute(sql, [participant_id] + timeframe_param)
                row = cursor.fetchone()
                return row.get("cnt") if row else 0

            # Distinct volunteer task types
            if target_metric == "volunteer_tasks_distinct":
                sql = (
                    "SELECT COUNT(DISTINCT eta.task_id) AS cnt "
                    "FROM Event_Task_Assignments eta JOIN Events e ON eta.event_id = e.id "
                    "WHERE eta.user_id = %s" + timeframe_clause_e
                )
                cursor.execute(sql, [participant_id] + timeframe_param)
                row = cursor.fetchone()
                return row.get("cnt") if row else 0

            # Distinct event types attended
            if target_metric == "event_types_distinct":
                sql = (
                    "SELECT COUNT(DISTINCT e.event_type) AS cnt "
                    "FROM Event_Results er JOIN Events e ON er.event_id = e.id "
                    "WHERE er.user_id = %s" + timeframe_clause_e
                )
                cursor.execute(sql, [participant_id] + timeframe_param)
                row = cursor.fetchone()
                return row.get("cnt") if row else 0

            # Distinct locations attended
            if target_metric == "locations_distinct":
                sql = (
                    "SELECT COUNT(DISTINCT e.town) AS cnt "
                    "FROM Event_Results er JOIN Events e ON er.event_id = e.id "
                    "WHERE er.user_id = %s" + timeframe_clause_e
                )
                cursor.execute(sql, [participant_id] + timeframe_param)
                row = cursor.fetchone()
                return row.get("cnt") if row else 0

            # Groups joined (active memberships)
            if target_metric == "groups_joined":
                sql = (
                    "SELECT COUNT(DISTINCT gm.group_id) AS cnt "
                    "FROM Group_Memberships gm WHERE gm.user_id = %s AND gm.member_status = 'active'"
                )
                cursor.execute(sql, (participant_id,))
                row = cursor.fetchone()
                return row.get("cnt") if row else 0

            # Volunteer hours - not explicitly stored; approximate by tasks count for now
            if target_metric == "volunteer_hours":
                sql = (
                    "SELECT COUNT(DISTINCT CONCAT(eta.event_id, '_', eta.task_id)) AS cnt "
                    "FROM Event_Task_Assignments eta JOIN Events e ON eta.event_id = e.id "
                    "WHERE eta.user_id = %s" + timeframe_clause_e
                )
                cursor.execute(sql, [participant_id] + timeframe_param)
                row = cursor.fetchone()
                return row.get("cnt") if row else 0

            return None

    def format_duration_seconds(self,seconds):
        return str(timedelta(seconds=seconds)) 

    def get_all_eventresults_for_participant(self,participant_id):
        with get_cursor() as cursor:
            try:
                cursor.execute("""
                    SELECT 
                        e.id AS event_id,
                        e.name AS event_name,
                        e.datetime AS event_date,
                        e.max_participants,
                        e.event_type,
                        e.town,
                        er.start_time,
                        er.end_time,
                        er.total_seconds,

                        ep.status AS participant_status,

                        completed.total_completed

                    FROM Events e

                    -- current user's participation status
                    INNER JOIN Event_Participants ep 
                        ON e.id = ep.event_id AND ep.user_id = %s

                    -- current user results
                    INNER JOIN Event_Results er 
                        ON e.id = er.event_id AND er.user_id = %s

                    -- participants in every event 
                    LEFT JOIN (
                        SELECT event_id, COUNT(DISTINCT user_id) AS total_completed
                        FROM Event_Results
                        GROUP BY event_id
                    ) completed ON completed.event_id = e.id

                    ORDER BY e.datetime DESC;
                """, (participant_id, participant_id))

                rows = cursor.fetchall()
                if not rows:
                    rows = []

            except Exception as e:
                print("SQL execution error:", e)
                rows = []

            # Initialize the statistical variables
            total_seconds = 0
            min_seconds = None

            for row in rows:
                raw_seconds = row.get('total_seconds')
                if raw_seconds is not None:
                    row['duration'] = self.format_duration_seconds(raw_seconds)
                    total_seconds += raw_seconds
                    if min_seconds is None or raw_seconds < min_seconds:
                        min_seconds = raw_seconds
                else:
                    row['duration'] = "no records"
            summary = {
                "total_duration": self.format_duration_seconds(total_seconds) if total_seconds else "00:00:00",
                "shortest_duration": self.format_duration_seconds(min_seconds) if min_seconds is not None else "no records",
                "events": rows
            }
            return summary
        
       
    def get_participant_result_for_event(self,participant_id, event_id,search_name):
       with get_cursor() as cursor:
            # 1. get all the participants for the event
            full_query = """
                SELECT 
                    ranked.event_id,
                    ranked.event_name,
                    ranked.event_date,
                    ranked.town,
                    ranked.event_type,
                    ranked.max_participants,
                    ranked.start_time,
                    ranked.end_time,
                    SEC_TO_TIME(ranked.total_seconds) AS formatted_duration,
                    ranked.participant_name,
                    ranked.user_id,
                    (
                        SELECT COUNT(*) + 1
                        FROM Event_Results er2
                        WHERE er2.event_id = ranked.event_id
                        AND er2.total_seconds < ranked.total_seconds
                    ) AS ranking
                FROM (
                    SELECT 
                        e.id AS event_id,
                        e.name AS event_name,
                        e.datetime AS event_date,
                        e.town,
                        e.event_type,
                        e.max_participants,
                        er.start_time,
                        er.end_time,
                        er.total_seconds,
                        CONCAT(u.first_name, ' ', u.last_name) AS participant_name,
                        u.id AS user_id
                    FROM Events e
                    INNER JOIN Event_Results er ON e.id = er.event_id
                    INNER JOIN Users u ON er.user_id = u.id
                    WHERE e.id = %s
                    ) AS ranked
            ORDER BY ranking ASC
            """
            cursor.execute(full_query, (event_id,))
            all_participants = cursor.fetchall()

            # if have search_name then filter
            if search_name:
                filtered_participants = [
                    p for p in all_participants
                    if search_name.lower() in p["participant_name"].lower()
                ]
            else:
                filtered_participants = all_participants

            # 2. get current user
            cursor.execute("""
                SELECT 
                    r.event_id,
                    r.event_name,
                    r.event_date,
                    r.town,
                    r.event_type,
                    r.max_participants,
                    SEC_TO_TIME(r.total_seconds) AS formatted_duration,
                    r.participant_name,
                    r.user_id,
                    (
                        SELECT COUNT(*) + 1
                        FROM Event_Results er2
                        WHERE er2.event_id = r.event_id
                        AND er2.total_seconds < r.total_seconds
                    ) AS ranking
                FROM (
                    SELECT 
                        e.id AS event_id,
                        e.name AS event_name,
                        e.datetime AS event_date,
                        e.town,
                        e.event_type,
                        e.max_participants,
                        er.total_seconds,
                        CONCAT(u.first_name, ' ', u.last_name) AS participant_name,
                        u.id AS user_id
                    FROM Events e
                    INNER JOIN Event_Results er ON e.id = er.event_id
                    INNER JOIN Users u ON er.user_id = u.id
                    WHERE e.id = %s AND u.id = %s
                ) r
            """, (event_id, participant_id))
            user_result = cursor.fetchone()
            return {
    "event": {
        "id": user_result["event_id"],
        "name": user_result["event_name"],
        "date": user_result["event_date"],
        "town": user_result["town"],
        "type": user_result["event_type"],
        "max_participants": user_result["max_participants"],
    },
    "user_result": {
        "user_id": user_result["user_id"],
        "name": user_result["participant_name"],
        "duration": user_result["formatted_duration"],
        "rank": user_result["ranking"],
    },
    "participants": filtered_participants,  
    "all_participants": all_participants   
}
    def format_duration(self,td):
      return str(td).split('.')[0] if td else None         
    def get_participant_result_for_event_statistics(self, event_id):
           with get_cursor() as cursor:
                cursor.execute("""
                    SELECT
                        COUNT(*) AS participant_count,
                        SEC_TO_TIME(AVG(total_seconds)) AS avg_duration,
                        SEC_TO_TIME(MIN(total_seconds)) AS fastest_duration,
                        SEC_TO_TIME(MAX(total_seconds)) AS slowest_duration
                    FROM
                        Event_Results
                    WHERE
                        event_id = %s;
                """, (event_id,))
                row = cursor.fetchone()
                return {
                    'participant_count': row['participant_count'],
                    'avg_duration': self.format_duration(row['avg_duration']),
                    'fastest_duration': self.format_duration(row['fastest_duration']),
                    'slowest_duration': self.format_duration(row['slowest_duration']),
                }
    def get_event_participant_durations(self, event_id,gender=None, age_group=None):
        with get_cursor() as cursor:
            query = """
                SELECT
                    CONCAT(u.first_name, ' ', u.last_name) AS full_name,
                    SEC_TO_TIME(er.total_seconds) AS raw_duration,
                    er.total_seconds
                FROM Event_Results er
                JOIN Users u ON er.user_id = u.id
                WHERE er.event_id = %s
            """
            params = [event_id]

            if gender:
                query += " AND u.gender = %s"
                params.append(gender)

            if age_group:
                if age_group.lower() == 'unknown':
                    query += " AND (u.age_group = %s OR u.age_group IS NULL)"
                    params.append('Unknown')
                else:
                    query += " AND u.age_group = %s"
                    params.append(age_group)

            query += " ORDER BY er.total_seconds ASC"

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            return [
                {
                    'name': row['full_name'],
                    'duration': self.format_duration(row['raw_duration']),
                    'total_seconds': row['total_seconds']
                }
                for row in rows
            ]
            
      
    def get_event_details_for_participant(self, participant_id, event_id):
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    e.id AS event_id,
                    e.name AS event_name,
                    e.datetime AS event_date,
                    e.event_type,
                    e.town,

                    -- current user results
                    er.total_seconds AS user_total_seconds,
                    SEC_TO_TIME(er.total_seconds) AS user_duration,

                    -- current user ranking
                    (
                        SELECT COUNT(*) + 1
                        FROM Event_Results er2
                        WHERE er2.event_id = e.id
                        AND er2.total_seconds < er.total_seconds
                    ) AS user_rank,

                    -- all user info
                    TIME_FORMAT(SEC_TO_TIME(MIN(er_all.total_seconds)), '%%H:%%i:%%s') AS fastest_time,
                    TIME_FORMAT(SEC_TO_TIME(MAX(er_all.total_seconds)), '%%H:%%i:%%s') AS slowest_time,
                    TIME_FORMAT(SEC_TO_TIME(AVG(er_all.total_seconds)), '%%H:%%i:%%s') AS average_time,
                    COUNT(er_all.user_id) AS total_participants

                FROM Events e

                -- current user results
                INNER JOIN Event_Results er ON e.id = er.event_id AND er.user_id = %s

                -- all other users results
                LEFT JOIN Event_Results er_all ON e.id = er_all.event_id

                WHERE e.id = %s
                GROUP BY e.id;
            """, (participant_id, event_id))
            return cursor.fetchone()

                   
    def get_all_events_for_participant(self, participant_id):
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    e.id AS event_id,
                    e.name AS event_name,
                    e.datetime AS event_date,
                    (
                        SELECT COUNT(*) + 1
                        FROM Event_Results er2
                        WHERE er2.event_id = e.id
                        AND er2.total_seconds < er.total_seconds
                    ) AS user_rank
                FROM Events e
                INNER JOIN Event_Results er ON e.id = er.event_id
                WHERE er.user_id = %s
                ORDER BY e.datetime DESC;
            """, (participant_id,))
            return cursor.fetchall()
                
                
    def get_personal_event_analysis_for_participant(self, participant_id):
        with get_cursor() as cursor:
            cursor.execute("""
                        SELECT 
                    e.id AS event_id,
                    e.name AS event_name,
                    e.datetime AS event_date,
                    e.event_type,
                    e.town,
                    er.total_seconds,
                    SEC_TO_TIME(er.total_seconds) AS formatted_duration,
                    (
                        SELECT COUNT(*) + 1
                        FROM Event_Results er2
                        WHERE er2.event_id = e.id
                          AND er2.total_seconds < er.total_seconds
                    ) AS user_rank
                FROM Events e
                INNER JOIN Event_Results er ON e.id = er.event_id
                WHERE er.user_id = %s
                ORDER BY e.datetime DESC;
            """, (participant_id,))
            return cursor.fetchall()
        
        
    def get_user_group_membership_results(self, participant_id):
        with get_cursor() as cursor:
            cursor.execute("""
                    SELECT
                        g.id AS group_id,
                        g.name AS group_name,
                        g.description AS group_description,
                        e.id AS event_id,
                        e.name AS event_name,
                        e.event_type,
                        e.town,
                        e.datetime AS event_date,
                        e.max_participants,
                        COUNT(DISTINCT ep.user_id) AS total_participants,
                        
                        -- current user result
                        er_user.start_time AS user_start_time,
                        er_user.end_time AS user_end_time,
                        er_user.total_seconds AS user_total_seconds,

                        -- current user ranking
                        (
                            SELECT COUNT(*) + 1
                            FROM Event_Results er2
                            WHERE er2.event_id = e.id
                            AND er2.total_seconds < er_user.total_seconds
                        ) AS user_rank,

                        --  top1 info
                        (SELECT CONCAT(u1.first_name, ' ', u1.last_name)
                        FROM Event_Results er1
                        JOIN Users u1 ON u1.id = er1.user_id
                        WHERE er1.event_id = e.id
                        ORDER BY er1.total_seconds ASC
                        LIMIT 1) AS first_user_name,
                        (SELECT er1.total_seconds
                        FROM Event_Results er1
                        WHERE er1.event_id = e.id
                        ORDER BY er1.total_seconds ASC
                        LIMIT 1) AS first_user_time,

                        --  top2 info
                        (SELECT CONCAT(u2.first_name, ' ', u2.last_name)
                        FROM Event_Results er2
                        JOIN Users u2 ON u2.id = er2.user_id
                        WHERE er2.event_id = e.id
                        ORDER BY er2.total_seconds ASC
                        LIMIT 1 OFFSET 1) AS second_user_name,
                        (SELECT er2.total_seconds
                        FROM Event_Results er2
                        WHERE er2.event_id = e.id
                        ORDER BY er2.total_seconds ASC
                        LIMIT 1 OFFSET 1) AS second_user_time,

                        -- top3 info
                        (SELECT CONCAT(u3.first_name, ' ', u3.last_name)
                        FROM Event_Results er3
                        JOIN Users u3 ON u3.id = er3.user_id
                        WHERE er3.event_id = e.id
                        ORDER BY er3.total_seconds ASC
                        LIMIT 1 OFFSET 2) AS third_user_name,
                        (SELECT er3.total_seconds
                        FROM Event_Results er3
                        WHERE er3.event_id = e.id
                        ORDER BY er3.total_seconds ASC
                        LIMIT 1 OFFSET 2) AS third_user_time

                    FROM Group_Memberships gm
                    JOIN Community_Groups g ON gm.group_id = g.id
                    JOIN Events e ON e.group_id = g.id
                    LEFT JOIN Event_Participants ep ON ep.event_id = e.id
                    LEFT JOIN Event_Results er_user 
                        ON er_user.event_id = e.id 
                        AND er_user.user_id = gm.user_id

                    WHERE gm.user_id = %s
                    AND er_user.total_seconds IS NOT NULL

                    GROUP BY 
                        g.id, g.name, g.description,
                        e.id, e.name, e.event_type, e.town, e.datetime, e.max_participants,
                        er_user.start_time, er_user.end_time, er_user.total_seconds

                    ORDER BY e.datetime DESC;
                """, (participant_id,))
            return cursor.fetchall()
        
        
    # participant_repository.py

    def get_top3_by_group(self,event_id, group_by="gender"):
        group_field = "u.gender" if group_by == "gender" else """
        CASE
            WHEN u.age < 18 THEN 'Under 18'
            WHEN u.age BETWEEN 18 AND 29 THEN '18-29'
            WHEN u.age BETWEEN 30 AND 44 THEN '30-44'
            ELSE '45+'
        END
    """

        query = f"""
            SELECT
                {group_field} AS group_label,
                CONCAT(u.first_name, ' ', u.last_name) AS full_name,
                er.total_seconds
            FROM Event_Results er
            JOIN Users u ON er.user_id = u.id
            WHERE er.event_id = %s
            ORDER BY group_label, er.total_seconds ASC
        """

        with get_cursor() as cursor:
            cursor.execute(query, (event_id,))
            return cursor.fetchall()
        
        
    def get_user_event_durations(self,user_id, event_type=None):
        query = """
            SELECT e.datetime, er.total_seconds, e.event_type
            FROM Event_Results er
            JOIN Events e ON er.event_id = e.id
            WHERE er.user_id = %s
        """
        params = [user_id]

        if event_type:
             query += " AND LOWER(e.event_type) LIKE LOWER(%s)"
             params.append(f"%{event_type}%")  

        query += " ORDER BY e.datetime"

        with get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_leaderboard_by_event_completions(self, time_window_days=None, group_id=None, gender=None, age_group=None):
        """Get leaderboard ranked by number of completed events"""
        with get_cursor() as cursor:
            query = """
                SELECT 
                    u.id AS user_id,
                    CONCAT(u.first_name, ' ', u.last_name) AS full_name,
                    u.town,
                    COUNT(DISTINCT er.event_id) AS events_completed,
                    MIN(er.total_seconds) AS best_time_seconds,
                    AVG(er.total_seconds) AS avg_time_seconds
                FROM Users u
                INNER JOIN Event_Results er ON u.id = er.user_id
                INNER JOIN Events e ON er.event_id = e.id
                WHERE u.global_role = 'participant'
            """
            params = []

            if group_id is not None:
                query += " AND EXISTS (SELECT 1 FROM Group_Memberships gm WHERE gm.user_id = u.id AND gm.group_id = %s AND gm.member_status = 'active')"
                params.append(group_id)
            
            if gender:
                if gender == 'unspecified':
                    query += " AND (u.gender IS NULL OR u.gender = '')"
                else:
                    query += " AND LOWER(u.gender) = %s"
                    params.append(gender.lower())

            if age_group:
                if age_group.lower() == 'unknown':
                    query += " AND (u.age_group = %s OR u.age_group IS NULL)"
                    params.append('Unknown')
                else:
                    query += " AND u.age_group = %s"
                    params.append(age_group)

            if time_window_days:
                query += " AND e.datetime >= DATE_SUB(NOW(), INTERVAL %s DAY)"
                params.append(time_window_days)
            
            query += """
                GROUP BY u.id, u.first_name, u.last_name, u.town
                ORDER BY events_completed DESC, avg_time_seconds ASC
                LIMIT 100
            """
            
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_leaderboard_by_points(self, time_window_days=None, group_id=None, gender=None, age_group=None):
        """Get leaderboard ranked by achievement points earned"""
        with get_cursor() as cursor:
            query = """
                SELECT 
                    u.id AS user_id,
                    CONCAT(u.first_name, ' ', u.last_name) AS full_name,
                    u.town,
                    COALESCE(SUM(a.points_reward), 0) AS total_points,
                    COUNT(DISTINCT ua.achievement_id) AS achievements_earned,
                    COUNT(DISTINCT er.event_id) AS events_completed
                FROM Users u
                LEFT JOIN User_Achievements ua ON u.id = ua.user_id
                LEFT JOIN Achievements a ON ua.achievement_id = a.id
                LEFT JOIN Event_Results er ON u.id = er.user_id
                WHERE u.global_role = 'participant'
            """
            params = []

            if group_id is not None:
                query += " AND EXISTS (SELECT 1 FROM Group_Memberships gm WHERE gm.user_id = u.id AND gm.group_id = %s AND gm.member_status = 'active')"
                params.append(group_id)
            
            if gender:
                if gender == 'unspecified':
                    query += " AND (u.gender IS NULL OR u.gender = '')"
                else:
                    query += " AND LOWER(u.gender) = %s"
                    params.append(gender.lower())

            if age_group:
                if age_group.lower() == 'unknown':
                    query += " AND (u.age_group = %s OR u.age_group IS NULL)"
                    params.append('Unknown')
                else:
                    query += " AND u.age_group = %s"
                    params.append(age_group)

            if time_window_days:
                query += " AND (ua.earned_at IS NULL OR ua.earned_at >= DATE_SUB(NOW(), INTERVAL %s DAY))"
                params.append(time_window_days)
            
            query += """
                GROUP BY u.id, u.first_name, u.last_name, u.town
                HAVING total_points > 0
                ORDER BY total_points DESC, achievements_earned DESC
                LIMIT 100
            """
            
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_leaderboard_by_volunteer_hours(self, time_window_days=None, group_id=None, gender=None, age_group=None):
        """Get leaderboard ranked by volunteer task participation"""
        with get_cursor() as cursor:
            query = """
                SELECT 
                    u.id AS user_id,
                    CONCAT(u.first_name, ' ', u.last_name) AS full_name,
                    u.town,
                    COUNT(DISTINCT CONCAT(eta.event_id, '_', eta.task_id)) AS volunteer_tasks_count,
                    COUNT(DISTINCT eta.event_id) AS events_volunteered
                FROM Users u
                INNER JOIN Event_Task_Assignments eta ON u.id = eta.user_id
                INNER JOIN Events e ON eta.event_id = e.id
                WHERE u.global_role = 'participant'
            """
            params = []

            if group_id is not None:
                query += " AND EXISTS (SELECT 1 FROM Group_Memberships gm WHERE gm.user_id = u.id AND gm.group_id = %s AND gm.member_status = 'active')"
                params.append(group_id)
            
            if gender:
                if gender == 'unspecified':
                    query += " AND (u.gender IS NULL OR u.gender = '')"
                else:
                    query += " AND LOWER(u.gender) = %s"
                    params.append(gender.lower())

            if age_group:
                if age_group == 'unknown':
                    query += " AND u.age_group IS NULL"
                else:
                    query += " AND u.age_group = %s"
                    params.append(age_group)

            if time_window_days:
                query += " AND e.datetime >= DATE_SUB(NOW(), INTERVAL %s DAY)"
                params.append(time_window_days)
            
            query += """
                GROUP BY u.id, u.first_name, u.last_name, u.town
                ORDER BY volunteer_tasks_count DESC, events_volunteered DESC
                LIMIT 100
            """
            
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_user_leaderboard_position(self, user_id, metric='events', time_window_days=None, group_id=None, gender=None, age_group=None):
        """Get a specific user's position in the leaderboard"""
        if metric == 'events':
            all_rankings = self.get_leaderboard_by_event_completions(time_window_days, group_id, gender, age_group)
        elif metric == 'points':
            all_rankings = self.get_leaderboard_by_points(time_window_days, group_id, gender, age_group)
        elif metric == 'volunteer':
            all_rankings = self.get_leaderboard_by_volunteer_hours(time_window_days, group_id, gender, age_group)
        else:
            return None
        
        for rank, entry in enumerate(all_rankings, start=1):
            if entry['user_id'] == user_id:
                return {'rank': rank, 'data': entry}
        
        return None

    
            
