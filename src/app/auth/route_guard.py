from functools import wraps
from typing import Callable

from flask import flash, redirect, url_for

from src.app.auth.auth_service import AuthService
from src.app.common.nav.encode import decode_id
from src.app.user.user import Role
def route_guard(*allowed_roles: Role) -> Callable:
    """
    Guard route by role(s).
    Example: @route_guard(Role.ADMIN, Role.PARTICIPANT)
    """
    def decorator(callback):
        @wraps(callback)
        def guard(*args, **kwargs):
            auth_service = AuthService()

            print("is_logged_in", auth_service.is_logged_in())
            if not auth_service.is_logged_in():
                flash("You must be logged in to view this page.", "warning")
                return redirect(url_for("app.login"))

            role = auth_service.get_user_role()
            print("role:", role)
            if role not in allowed_roles:
                flash("You do not have permission to view this page.", "danger")
                return redirect(url_for("app.home"))

            # User cannot view information of others
            param = {
                Role.ADMIN: "encoded_admin_id",
                Role.PARTICIPANT: "encoded_participant_id",
                Role.VOLUNTEER: "encoded_volunteer_id",
            }.get(role)

            resource_id = decode_id(kwargs.get(param))
            if resource_id is not None:

                user_id = auth_service.get_user_id()
                print(f"DEBUG route_guard: URL resource_id={resource_id}, user_id={user_id}, param={param}")
                if str(resource_id) != str(user_id):
                    flash("You are not authorised to view this page.", "danger")
                    return redirect(url_for("app.home"))

            return callback(*args, **kwargs)
        return guard
    return decorator


