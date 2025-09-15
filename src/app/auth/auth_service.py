import os
from flask import session
from typing import Optional

from src.app.user.user import Role
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

    def login(self, user_id: int, role: Role):
        session['user_id'] = user_id
        session['role'] = role.value


    def logout(self):
        session.clear()

    def is_logged_in(self) -> bool:
        return self.get_user_id() is not None

    def get_user_id(self) -> int:
        return session.get('user_id')


    def get_user_resource_id(self) -> str:
        "Get the encoded user ID for resource access control"
        user_id = self.get_user_id()
        return encode_id(user_id) if user_id else None


    def get_user_role(self) -> Role:
        role_str = session.get('role')
        if role_str:
            return Role(role_str)
        return None

    def is_admin(self) -> bool:
        return self.get_user_role() == Role.ADMIN

    def is_participant(self) -> bool:
        return self.get_user_role() == Role.PARTICIPANT

    def is_volunteer(self) -> bool:
        return self.get_user_role() == Role.VOLUNTEER
    
auth_service = AuthService()    
    