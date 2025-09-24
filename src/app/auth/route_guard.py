from functools import wraps
from typing import Callable

from flask import flash, redirect, url_for

from src.app.auth.auth_service import AuthService
from src.app.common.nav.encode import decode_id
from src.app.user.user import GlobalRole


def require_login(callback):
    """
    Require user to be logged in
    """
    @wraps(callback)
    def guard(*args, **kwargs):
        auth_service = AuthService()
        
        if not auth_service.is_logged_in():
            flash("You must be logged in to view this page.", "warning")
            return redirect(url_for("app.login"))
        
        return callback(*args, **kwargs)
    return guard


def require_super_admin(callback):
    """
    Require user to be a super admin
    """
    @wraps(callback)
    def guard(*args, **kwargs):
        auth_service = AuthService()
        
        if not auth_service.is_logged_in():
            flash("You must be logged in to view this page.", "warning")
            return redirect(url_for("app.login"))
        
        if not auth_service.is_super_admin():
            flash("You do not have permission to view this page.", "danger")
            return redirect(url_for("app.home"))
        
        return callback(*args, **kwargs)
    return guard


def require_participant(callback):
    """
    Require user to be a participant (or super admin)
    """
    @wraps(callback)
    def guard(*args, **kwargs):
        auth_service = AuthService()
        
        if not auth_service.is_logged_in():
            flash("You must be logged in to view this page.", "warning")
            return redirect(url_for("app.login"))
        
        if not (auth_service.is_participant() or auth_service.is_super_admin()):
            flash("You do not have permission to view this page.", "danger")
            return redirect(url_for("app.home"))
        
        return callback(*args, **kwargs)
    return guard


def require_group_manager(group_id_param='group_id'):
    """
    Require user to be a manager of the specified group (or super admin)
    """
    def decorator(callback):
        @wraps(callback)
        def guard(*args, **kwargs):
            from src.app.group.group_service import GroupService
            
            auth_service = AuthService()
            
            if not auth_service.is_logged_in():
                flash("You must be logged in to view this page.", "warning")
                return redirect(url_for("app.login"))
            
            # Get group_id from kwargs
            group_id = kwargs.get(group_id_param)
            if not group_id:
                flash("Invalid group specified.", "danger")
                return redirect(url_for("app.home"))
            
            user_id = auth_service.get_user_id()
            is_super_admin = auth_service.is_super_admin()
            
            if not GroupService.can_user_manage_group(group_id, user_id, is_super_admin):
                flash("You do not have permission to manage this group.", "danger")
                return redirect(url_for("groups.view_group", group_id=group_id))
            
            return callback(*args, **kwargs)
        return guard
    return decorator


