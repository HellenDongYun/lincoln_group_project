import re

from email_validator import validate_email, EmailNotValidError
from flask_bcrypt import check_password_hash

from src.app.user.user import User, Role
from src.app.user.user import User
from src.app.user.user_repository import UserRepository

NAME_REGEX = r"^[A-Za-zÀ-ÖØ-öø-ÿ' -]+$"
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$"

class UserService:

    def __init__(self):
        self.repository = UserRepository()

    def get_user_by_email(self, email: str) -> User:
        row = self.repository.get_user_by_email(email)
        return User(**row) if row else None

    def create_user(self, user: tuple) -> bool:
        return self.repository.create_user(user)

    def validate_name_input(self, name_input: str, field_name: str) -> list[str]:
        errors = []

        name_input = name_input.strip()

        if not name_input:
            errors.append(f"Please enter your {field_name.lower()}.")
        elif len(name_input) > 100:
            errors.append(f"{field_name} cannot exceed 100 characters.")
        elif not re.match(NAME_REGEX, name_input):
            errors.append(f"{field_name} contains invalid characters.")

        return errors

    def validate_email_input(self, email_input: str, exclude_user_id: int = None) -> tuple[list[str], str] :
        errors = []

        email_input = email_input.strip()

        if not email_input:
            errors.append("Please enter your email address.")
            return errors, None

        try:
            normalised_email = validate_email(email_input).normalized
        except EmailNotValidError as exception:
            errors.append(str(exception))
            return errors, None

        existing_user = self.repository.get_user_by_email(normalised_email)
        if existing_user and (exclude_user_id is None or existing_user.get('id') != exclude_user_id):
            errors.append("An account with this email already exists.")

        return errors, normalised_email

    def validate_password_input(self, password_input: str) -> list[str]:
        errors = []

        password_input = password_input.strip()

        if not password_input:
            errors.append(f"Please enter your password.")
        elif len(password_input) < 8:
            errors.append("Password must be at least 8 characters long.")
        elif not re.match(PASSWORD_REGEX, password_input):
            errors.append("Password must have at least 1 lower case, 1 upper case, 1 number and 1 special character.")

        return errors

    def validate_user(self, email: str, password: str) -> User:
        """Validate user credentials and return user object if valid"""
        if not email or not password:
            return None

        # Get user from database
        user_data = self.repository.get_user_by_email(email.strip())
        if not user_data:
            return None

        # Check if user is active
        if user_data.get('status') == 'inactive':
            return None

        # Check password
        if not check_password_hash(user_data['password_hash'], password):
            return None


        # Convert role string to Role enum
        if 'role' in user_data and user_data['role']:
            try:
                user_data['role'] = Role(user_data['role'])
            except ValueError:
                user_data['role'] = Role.PARTICIPANT  # Default fallback

        # Return user object
        return User(**user_data)

    def get_user_by_id(self, user_id: int) -> dict:
        """Get user by ID"""
        return self.repository.get_user_by_id(user_id)

    def update_user(self, user_id: int, update_data: dict) -> bool:
        """Update user information"""
        return self.repository.update_user(user_id, update_data)
