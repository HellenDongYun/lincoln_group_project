from src.app.common.db.repository import Repository
from src.app.common.db.cursor import get_cursor


class VolunteerRepository(Repository):
    
    def get_available_opportunities(self, volunteer_id=None):
        """Get all volunteer opportunities with available vacancies"""
        if volunteer_id:
            # Exclude events where the volunteer is already signed up for any role
            # AND exclude events on dates where the volunteer has another commitment
            sql = """
                SELECT DISTINCT
                    e.id as Event_ID,
                    e.name as Event_Name,
                    DATE(e.datetime) as Event_Date,
                    e.town as Event_Location,
                    vr.id as Role_ID,
                    vr.name as Role_Name,
                    v.spots as Number_of_Positions,
                    COALESCE(COUNT(ev.volunteer_id), 0) as Current_Signups,
                    (v.spots - COALESCE(COUNT(ev.volunteer_id), 0)) as Available_Spots
                FROM Events e
                JOIN Vacancies v ON e.id = v.event_id
                JOIN Volunteer_Roles vr ON v.role_id = vr.id
                LEFT JOIN Event_Volunteers ev ON e.id = ev.event_id AND vr.id = ev.role_id
                WHERE DATE(e.datetime) >= CURDATE()
                AND e.id NOT IN (
                    SELECT DISTINCT event_id 
                    FROM Event_Volunteers 
                    WHERE volunteer_id = %s
                )
                AND DATE(e.datetime) NOT IN (
                    SELECT DISTINCT DATE(e2.datetime)
                    FROM Event_Volunteers ev2
                    JOIN Events e2 ON ev2.event_id = e2.id
                    WHERE ev2.volunteer_id = %s
                )
                GROUP BY e.id, e.name, DATE(e.datetime), e.town, vr.id, vr.name, v.spots
                HAVING Available_Spots > 0
                ORDER BY DATE(e.datetime) ASC, e.name ASC, vr.name ASC
            """
            params = (volunteer_id, volunteer_id)
        else:
            # Show all available opportunities
            sql = """
                SELECT DISTINCT
                    e.id as Event_ID,
                    e.name as Event_Name,
                    DATE(e.datetime) as Event_Date,
                    e.town as Event_Location,
                    vr.id as Role_ID,
                    vr.name as Role_Name,
                    v.spots as Number_of_Positions,
                    COALESCE(COUNT(ev.volunteer_id), 0) as Current_Signups,
                    (v.spots - COALESCE(COUNT(ev.volunteer_id), 0)) as Available_Spots
                FROM Events e
                JOIN Vacancies v ON e.id = v.event_id
                JOIN Volunteer_Roles vr ON v.role_id = vr.id
                LEFT JOIN Event_Volunteers ev ON e.id = ev.event_id AND vr.id = ev.role_id
                WHERE DATE(e.datetime) >= CURDATE()
                GROUP BY e.id, e.name, DATE(e.datetime), e.town, vr.id, vr.name, v.spots
                HAVING Available_Spots > 0
                ORDER BY DATE(e.datetime) ASC, e.name ASC, vr.name ASC
            """
            params = ()
        
        try:
            return self.fetchall(sql, params)
        except Exception as e:
            # Return empty list if tables don't exist
            print(f"Database error in get_available_opportunities: {e}")
            return []
    
    def get_volunteer_roles(self, volunteer_id):
        """Get all roles that a volunteer is currently signed up for"""
        sql = """
            SELECT 
                e.id as Event_ID,
                e.name as Event_Name,
                DATE(e.datetime) as Event_Date,
                e.town as Event_Location,
                vr.id as Role_ID,
                vr.name as Role_Name,
                CURDATE() as Signup_Date
            FROM Event_Volunteers ev
            JOIN Events e ON ev.event_id = e.id
            JOIN Volunteer_Roles vr ON ev.role_id = vr.id
            WHERE ev.volunteer_id = %s
            AND DATE(e.datetime) >= CURDATE()
            ORDER BY DATE(e.datetime) ASC, e.name ASC, vr.name ASC
        """
        try:
            return self.fetchall(sql, (volunteer_id,))
        except Exception as e:
            # Return empty list if tables don't exist
            print(f"Database error in get_volunteer_roles: {e}")
            return []
    
    def get_past_volunteer_roles(self, volunteer_id):
        """Get all past volunteer roles that a volunteer has completed"""
        sql = """
            SELECT 
                e.id as Event_ID,
                e.name as Event_Name,
                e.event_type as Event_Type,
                DATE(e.datetime) as Event_Date,
                e.town as Event_Location,
                vr.id as Role_ID,
                vr.name as Role_Name,
                CURDATE() as Signup_Date
            FROM Event_Volunteers ev
            JOIN Events e ON ev.event_id = e.id
            JOIN Volunteer_Roles vr ON ev.role_id = vr.id
            WHERE ev.volunteer_id = %s
            AND DATE(e.datetime) < CURDATE()
            ORDER BY DATE(e.datetime) DESC, e.name ASC, vr.name ASC
        """
        try:
            return self.fetchall(sql, (volunteer_id,))
        except Exception as e:
            # Return empty list if tables don't exist
            print(f"Database error in get_past_volunteer_roles: {e}")
            return []
    
    def has_vacancy(self, event_id, role_id):
        """Check if there are still vacancies for a specific role at an event"""
        sql = """
            SELECT 
                v.spots as Number_of_Positions,
                COALESCE(COUNT(ev.volunteer_id), 0) as Current_Signups
            FROM Vacancies v
            LEFT JOIN Event_Volunteers ev ON v.event_id = ev.event_id AND v.role_id = ev.role_id
            WHERE v.event_id = %s AND v.role_id = %s
            GROUP BY v.event_id, v.role_id, v.spots
        """
        try:
            result = self.fetchall(sql, (event_id, role_id))
            if result:
                row = result[0]
                positions = row['Number_of_Positions'] if isinstance(row, dict) else row[0]
                current_signups = row['Current_Signups'] if isinstance(row, dict) else row[1]
                return current_signups < positions
            else:
                # No vacancy record exists for this role/event combination
                return False
        except Exception:
            return False
    
    def is_already_signed_up(self, volunteer_id, event_id, role_id):
        """Check if a volunteer is already signed up for a specific role at an event"""
        sql = """
            SELECT COUNT(*) as count_result
            FROM Event_Volunteers 
            WHERE volunteer_id = %s AND event_id = %s AND role_id = %s
        """
        try:
            result = self.fetchall(sql, (volunteer_id, event_id, role_id))
            if result:
                row = result[0]
                count = row['count_result'] if isinstance(row, dict) else row[0]
                return count > 0
            return False
        except Exception:
            return False
    
    def is_signed_up_for_event(self, volunteer_id, event_id):
        """Check if a volunteer is already signed up for ANY role at an event"""
        sql = """
            SELECT COUNT(*) as count_result
            FROM Event_Volunteers 
            WHERE volunteer_id = %s AND event_id = %s
        """
        try:
            result = self.fetchall(sql, (volunteer_id, event_id))
            if result:
                row = result[0]
                count = row['count_result'] if isinstance(row, dict) else row[0]
                return count > 0
            return False
        except Exception:
            return False
    
    def is_signed_up_for_same_date(self, volunteer_id, event_id):
        """Check if a volunteer is already signed up for another event on the same date"""
        sql = """
            SELECT COUNT(*) as count_result
            FROM Event_Volunteers ev1
            JOIN Events e1 ON ev1.event_id = e1.id
            JOIN Events e2 ON e2.id = %s
            WHERE ev1.volunteer_id = %s 
            AND ev1.event_id != %s
            AND DATE(e1.datetime) = DATE(e2.datetime)
        """
        try:
            result = self.fetchall(sql, (event_id, volunteer_id, event_id))
            if result:
                row = result[0]
                count = row['count_result'] if isinstance(row, dict) else row[0]
                return count > 0
            return False
        except Exception:
            return False
    
    def signup_for_role(self, volunteer_id, event_id, role_id):
        """Sign up a volunteer for a specific role at an event"""
        sql = """
            INSERT INTO Event_Volunteers (volunteer_id, event_id, role_id) 
            VALUES (%s, %s, %s)
        """
        try:
            with get_cursor() as cursor:
                cursor.execute(sql, (volunteer_id, event_id, role_id))
                return True
        except Exception:
            return False
    
    def cancel_role(self, volunteer_id, event_id, role_id):
        """Cancel a volunteer's sign-up for a specific role"""
        sql = """
            DELETE FROM Event_Volunteers 
            WHERE volunteer_id = %s AND event_id = %s AND role_id = %s
        """
        try:
            with get_cursor() as cursor:
                cursor.execute(sql, (volunteer_id, event_id, role_id))
                return cursor.rowcount > 0
        except Exception:
            return False
