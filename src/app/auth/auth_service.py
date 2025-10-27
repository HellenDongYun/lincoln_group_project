import os
from flask import session

from src.app.user.user import GlobalRole, Role
from src.app.common.nav.encode import encode_id


"""
A singleton service for managing user authentication using Flask sessions.

This service provides methods to log in and log out users, 
check login status, and perform role based checks.
"""
class AuthService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuthService, cls).__new__(cls)
        return cls._instance

    def login(self, user_id: int, global_role: GlobalRole):
        session['user_id'] = user_id
        session['global_role'] = global_role.value

    def logout(self):
        session.clear()

    def is_logged_in(self) -> bool:
        return self.get_user_id() is not None

    def get_user_id(self):
        return session.get('user_id')

    def get_user_resource_id(self):
        "Get the encoded user ID for resource access control"
        user_id = self.get_user_id()
        return encode_id(user_id) if user_id else None

    def get_global_role(self):
        role_str = session.get('global_role')
        if role_str:
            return GlobalRole(role_str)
        return None

    def is_super_admin(self) -> bool:
        return self.get_global_role() == GlobalRole.SUPER_ADMIN

    def is_participant(self) -> bool:
        return self.get_global_role() == GlobalRole.PARTICIPANT

    def is_support_technician(self) -> bool:
        return self.get_global_role() == GlobalRole.SUPPORT_TECHNICIAN

    # Legacy methods for backward compatibility
    def get_user_role(self):
        global_role = self.get_global_role()
        if global_role == GlobalRole.SUPER_ADMIN:
            return Role.ADMIN
        elif global_role == GlobalRole.PARTICIPANT:
            return Role.PARTICIPANT
        elif global_role == GlobalRole.SUPPORT_TECHNICIAN:
            return Role.ADMIN
        return None

    def is_admin(self) -> bool:
        return self.is_super_admin()

    def is_volunteer(self) -> bool:
        # Volunteering is task-based, not  role
        return False
    
auth_service = AuthService()    
    