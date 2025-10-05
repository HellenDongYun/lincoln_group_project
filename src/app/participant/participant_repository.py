from src.app.common.db.cursor import get_cursor
from src.app.common.db.repository import Repository


class ParticipantRepository(Repository):
    
    """
    参与者仓储类，用于处理参与者相关的数据库操作。
    继承自Repository基类，提供参与者相关数据访问方法。
    """
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
                COALESCE(COUNT(p.participant_id), 0) as Current_Registrations,
                (e.max_participants - COALESCE(COUNT(p.participant_id), 0)) as Available_Spots
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
                e.id as Event_ID,
                e.name as Event_Name,
                DATE(e.datetime) as Event_Date,
                e.town as Event_Location,
                e.event_type as Event_Type,
                rr.start_time as Start_Time,
                rr.end_time as End_Time,
                SEC_TO_TIME(TIME_TO_SEC(TIMEDIFF(rr.end_time, rr.start_time))) as Race_Time,
                TIME_TO_SEC(TIMEDIFF(rr.end_time, rr.start_time)) as Race_Time_Seconds,
                RANK() OVER (
                    PARTITION BY rr.event_id 
                    ORDER BY TIME_TO_SEC(TIMEDIFF(rr.end_time, rr.start_time))
                ) as Position,
                (
                    SELECT COUNT(*) 
                    FROM Event_Results rr2 
                    WHERE rr2.event_id = rr.event_id
                ) as Total_Participants
            FROM Event_Results rr
            JOIN Events e ON rr.event_id = e.id
            WHERE rr.participant_id = %s
            AND DATE(e.datetime) < CURDATE()
            AND rr.start_time IS NOT NULL 
            AND rr.end_time IS NOT NULL
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
    
    
    def show_application(self,status, page,per_page,participant_id):
        """Show the applications for a participant"""
        query = '''
        SELECT 
            ga.proposed_name AS name,
            ga.proposed_description AS description,
            ga.proposed_town AS town,
            ga.visibility,
            ga.status,
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

    def create_group_application(self,participant_id, name, description, town, visibility):
        with get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO Group_Applications (
                    applicant_id, proposed_name, proposed_description, proposed_town, visibility
                ) VALUES (%s, %s, %s, %s, %s)
            """, (participant_id, name, description, town, visibility)) 
            
    def get_application_by_id(self,participant_id, application_id):
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM Group_Applications WHERE id = %s AND applicant_id = %s
            """, (application_id, participant_id))
            return cursor.fetchone()
        
    def update_group_application(self,participant_id, application_id, name, town, visibility, description):
        with get_cursor() as cursor:
            cursor.execute("""
                UPDATE Group_Applications 
                SET proposed_name = %s, proposed_town = %s, visibility = %s, proposed_description = %s
                WHERE id = %s AND applicant_id = %s
            """, (name, town, visibility, description, application_id, participant_id))
    
    
    
    def delete_group_application(self,participant_id, application_id):
        with get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM Group_Applications WHERE id = %s AND applicant_id = %s
            """, (application_id, participant_id))