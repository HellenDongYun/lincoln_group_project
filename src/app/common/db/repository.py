from src.app.common.db.cursor import get_cursor


class Repository:

    def fetchall(self, query: str, params: tuple = ()) -> list[dict]:
        with get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def fetchone(self, query: str, params: tuple = ()) -> dict:
        with get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def execute(self, query: str, params: tuple = ()) -> int:
        """Execute a query and return the number of affected rows"""
        with get_cursor() as cursor:
            result = cursor.execute(query, params)

            return result
    def home_filter_events(limit,location="", event_type="", date_str=""):
        base_query = "SELECT * FROM Events WHERE 1=1"
        params = []
        if location:
            base_query += " AND town LIKE %s"
            params.append(f"%{location}%")
        if event_type and event_type != "all":
            base_query += " AND name LIKE %s"
            params.append(f"%{event_type}%")
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                base_query += " AND DATE(datetime) = %s"
                params.append(date_obj.date())
            except ValueError:
                pass
        base_query += " ORDER BY datetime ASC LIMIT {}".format(int(limit))
        with get_cursor() as cursor:
            cursor.execute(base_query, params)
            return cursor.fetchall()     
    def home_filter_groups():
        with get_cursor() as cursor:
            query = """
            SELECT 
            cg.id AS group_id,
            cg.name AS group_name,
            cg.description,
            cg.town AS group_town,
            cg.visibility,
            cg.status AS group_status,
            COUNT(gm.user_id) AS total_members,
            SUM(gm.member_status = 'active') AS active_members,
            SUM(gm.group_role = 'manager') AS manager_count
            FROM Community_Groups cg
            LEFT JOIN Group_Memberships gm ON cg.id = gm.group_id
            GROUP BY cg.id, cg.name, cg.description, cg.town, cg.visibility, cg.status
            ORDER BY cg.name;
            """
            cursor.execute(query)
            return cursor.fetchall()   
        

