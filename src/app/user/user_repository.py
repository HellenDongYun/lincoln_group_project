from src.app.common.db.cursor import get_cursor
from src.app.common.db.repository import Repository


class UserRepository(Repository):

    def get_user_by_email(self, email: str):
        return self.fetchone(
            """
            SELECT
                *
            FROM Users
            WHERE email = %s;
            """,
            (email,)
        )

    def create_user(self, user: tuple) -> bool:
        try:
            first_name, last_name, town, email, password_hash, *rest = user
            role = rest[0] if rest else None

            with get_cursor() as cursor:
                if role is None:
                    cursor.execute(
                        """
                        INSERT INTO Users (first_name, last_name, town, email, password_hash)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (first_name, last_name, town, email, password_hash)
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO Users (first_name, last_name, town, email, password_hash, role)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (first_name, last_name, town, email, password_hash, role)
                    )
            return True
        except Exception as exception:
            print(f"Create user failed: {exception}")
            return False

    def get_user_by_email(self, email: str) -> dict:
        """Get user by email address"""
        return self.fetchone(
            "SELECT * FROM Users WHERE email = %s",
            (email,)
        )

    def get_user_by_id(self, user_id: int) -> dict:
        """Get user by ID"""
        return self.fetchone(
            "SELECT * FROM Users WHERE id = %s",
            (user_id,)
        )

    def update_user(self, user_id: int, update_data: dict) -> bool:
        """Update user information"""
        try:
            # Build dynamic SQL based on fields to update
            set_clauses = []
            values = []
            
            for field, value in update_data.items():
                if field in ['first_name', 'last_name', 'town', 'email', 'password_hash']:
                    set_clauses.append(f"{field} = %s")
                    values.append(value)
            
            if not set_clauses:
                return False
            
            values.append(user_id)
            
            with get_cursor() as cursor:
                sql = f"UPDATE Users SET {', '.join(set_clauses)} WHERE id = %s"
                cursor.execute(sql, tuple(values))
            
            return True
        except Exception as exception:
            print(f"Update user failed: {exception}")
            return False



