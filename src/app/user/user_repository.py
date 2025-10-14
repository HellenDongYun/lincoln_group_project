from src.app.common.db.cursor import get_cursor
from src.app.common.db.repository import Repository


class UserRepository(Repository):

    def create_user(self, user: tuple) -> bool:
        try:
            first_name, last_name, town, email, password_hash, *rest = user
            # rest may contain [global_role, gender, age]
            global_role = 'participant'
            gender = None
            age = None
            if len(rest) > 0:
                global_role = rest[0] or 'participant'
            if len(rest) > 1:
                gender = rest[1]
            if len(rest) > 2:
                age = rest[2]

            with get_cursor() as cursor:
                # Build dynamic insert to include gender and age when provided
                columns = ["first_name", "last_name", "town", "email", "password_hash", "global_role"]
                values = [first_name, last_name, town, email, password_hash, global_role]
                if gender is not None:
                    columns.append("gender")
                    values.append(gender)
                if age is not None:
                    columns.append("age")
                    values.append(age)

                placeholders = ", ".join(["%s"] * len(values))
                sql = f"INSERT INTO Users ({', '.join(columns)}) VALUES ({placeholders})"
                cursor.execute(sql, tuple(values))
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
                if field in ['first_name', 'last_name', 'town', 'email', 'password_hash', 'global_role', 'gender', 'age']:
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



