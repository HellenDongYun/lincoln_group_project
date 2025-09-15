from src.app.common.db.repository import Repository
from src.app.common.db.cursor import get_cursor


class ResultsRepository(Repository):
    
    def get_events_with_results(self):
        """Get all events that have race results"""
        sql = """
            SELECT DISTINCT
                e.id as Event_ID,
                e.name as Event_Name,
                DATE(e.datetime) as Event_Date,
                e.town as Event_Location,
                e.event_type as Event_Type,
                COUNT(rr.participant_id) as Result_Count
            FROM Events e
            JOIN Race_Results rr ON e.id = rr.event_id
            GROUP BY e.id, e.name, DATE(e.datetime), e.town, e.event_type
            ORDER BY DATE(e.datetime) DESC, e.name ASC
        """
        try:
            return self.fetchall(sql)
        except Exception as e:
            print(f"Database error in get_events_with_results: {e}")
            return []
    
    def get_all_events(self):
        """Get all events for the upload dropdown"""
        sql = """
            SELECT 
                id as Event_ID,
                name as Event_Name,
                DATE(datetime) as Event_Date,
                town as Event_Location,
                event_type as Event_Type
            FROM Events
            WHERE DATE(datetime) >= CURDATE() - INTERVAL 30 DAY
            ORDER BY datetime ASC
        """
        try:
            return self.fetchall(sql)
        except Exception as e:
            print(f"Database error in get_all_events: {e}")
            return []
    
    def get_event_details(self, event_id):
        """Get details for a specific event"""
        sql = """
            SELECT 
                id as Event_ID,
                name as Event_Name,
                DATE(datetime) as Event_Date,
                TIME(datetime) as Event_Time,
                town as Event_Location,
                event_type as Event_Type,
                description as Event_Description,
                max_participants as Max_Participants
            FROM Events
            WHERE id = %s
        """
        try:
            result = self.fetchall(sql, (event_id,))
            return result[0] if result else None
        except Exception as e:
            print(f"Database error in get_event_details: {e}")
            return None
    
    def get_event_results(self, event_id):
        """Get race results for a specific event with calculated race times"""
        sql = """
            SELECT 
                rr.participant_id as Participant_ID,
                u.first_name as First_Name,
                u.last_name as Last_Name,
                u.email as Email,
                u.town as Town,
                rr.start_time as Start_Time,
                rr.end_time as End_Time,
                TIME_TO_SEC(TIMEDIFF(rr.end_time, rr.start_time)) as Race_Time_Seconds,
                SEC_TO_TIME(TIME_TO_SEC(TIMEDIFF(rr.end_time, rr.start_time))) as Race_Time,
                RANK() OVER (ORDER BY TIME_TO_SEC(TIMEDIFF(rr.end_time, rr.start_time))) as Position
            FROM Race_Results rr
            JOIN Users u ON rr.participant_id = u.id
            WHERE rr.event_id = %s
            AND rr.start_time IS NOT NULL 
            AND rr.end_time IS NOT NULL
            ORDER BY Race_Time_Seconds ASC
        """
        try:
            return self.fetchall(sql, (event_id,))
        except Exception as e:
            print(f"Database error in get_event_results: {e}")
            return []
    
    def get_participant_id_by_email(self, email):
        """Get participant ID by email address"""
        sql = """
            SELECT p.participant_id
            FROM Participants p
            JOIN Users u ON p.participant_id = u.id
            WHERE u.email = %s
        """
        try:
            result = self.fetchall(sql, (email,))
            if result:
                row = result[0]
                return row['participant_id'] if isinstance(row, dict) else row[0]
            return None
        except Exception as e:
            print(f"Database error in get_participant_id_by_email: {e}")
            return None
    
    def validate_participant_exists(self, participant_id):
        """Validate that a participant ID exists in the database"""
        sql = """
            SELECT COUNT(*) as count
            FROM Users u
            WHERE u.id = %s AND u.role = 'participant'
        """
        try:
            result = self.fetchone(sql, (participant_id,))
            return result['count'] > 0 if result else False
        except Exception as e:
            print(f"Database error in validate_participant_exists: {e}")
            return False
    
    def validate_participant_registered_for_event(self, event_id, participant_id):
        """Validate that a participant is registered for a specific event"""
        sql = """
            SELECT COUNT(*) as count
            FROM Participants p
            WHERE p.event_id = %s AND p.participant_id = %s AND p.status = 'registered'
        """
        try:
            print(f"DEBUG REPO: Checking registration for event_id={event_id}, participant_id={participant_id}")
            result = self.fetchone(sql, (event_id, participant_id))
            print(f"DEBUG REPO: Query result: {result}")
            count = result['count'] if result else 0
            print(f"DEBUG REPO: Count: {count}, returning: {count > 0}")
            return count > 0
        except Exception as e:
            print(f"Database error in validate_participant_registered_for_event: {e}")
            return False
    
    def get_participant_info(self, participant_id):
        """Get participant information by ID"""
        sql = """
            SELECT id, first_name, last_name, email
            FROM Users
            WHERE id = %s AND role = 'participant'
        """
        try:
            result = self.fetchone(sql, (participant_id,))
            return result if result else None
        except Exception as e:
            print(f"Database error in get_participant_info: {e}")
            return None
    
    def get_participant_info_by_email(self, email):
        """Get participant information by email"""
        sql = """
            SELECT id, first_name, last_name, email
            FROM Users
            WHERE email = %s AND role = 'participant'
        """
        try:
            result = self.fetchone(sql, (email,))
            return result if result else None
        except Exception as e:
            print(f"Database error in get_participant_info_by_email: {e}")
            return None
    
    def save_race_result(self, event_id, participant_id, start_time, end_time):
        """Save or update race result for a participant"""
        sql = """
            INSERT INTO Race_Results (event_id, participant_id, start_time, end_time)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                start_time = VALUES(start_time),
                end_time = VALUES(end_time)
        """
        try:
            with get_cursor() as cursor:
                cursor.execute(sql, (event_id, participant_id, start_time, end_time))
                return True
        except Exception as e:
            print(f"Database error in save_race_result: {e}")
            return False

    def check_existing_results(self, event_id):
        """Check if an event already has race results"""
        sql = """
            SELECT COUNT(*) as result_count
            FROM Race_Results
            WHERE event_id = %s
        """
        try:
            result = self.fetchone(sql, (event_id,))
            return result['result_count'] if result else 0
        except Exception as e:
            print(f"Database error in check_existing_results: {e}")
            return 0
    
    def remove_event_results(self, event_id):
        """Remove all race results for a specific event"""
        sql = """
            DELETE FROM Race_Results
            WHERE event_id = %s
        """
        try:
            with get_cursor() as cursor:
                cursor.execute(sql, (event_id,))
                return cursor.rowcount
        except Exception as e:
            print(f"Database error in remove_event_results: {e}")
            return 0
    
    def get_event_result_summary(self, event_id):
        """Get summary of existing results for an event"""
        sql = """
            SELECT 
                COUNT(*) as total_results,
                MIN(start_time) as earliest_start,
                MAX(end_time) as latest_finish
            FROM Race_Results
            WHERE event_id = %s
        """
        try:
            return self.fetchone(sql, (event_id,))
        except Exception as e:
            print(f"Database error in get_event_result_summary: {e}")
            return None

    def get_event_start_time(self, event_id):
        """Get the start datetime for an event"""
        sql = """
            SELECT datetime
            FROM Events
            WHERE id = %s
        """
        try:
            result = self.fetchone(sql, (event_id,))
            return result['datetime'] if result else None
        except Exception as e:
            print(f"Database error in get_event_start_time: {e}")
            return None
