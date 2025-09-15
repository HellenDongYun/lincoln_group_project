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