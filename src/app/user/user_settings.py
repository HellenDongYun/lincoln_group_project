import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from src.app import db  
from src.app.models import User  

settings_bp = Blueprint("settings", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@settings_bp.route("/settings", methods=["GET", "POST"])
@login_required
def update_settings():
    errors = {}

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        skills = request.form.get("skills")
        bio = request.form.get("bio")

        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        file = request.files.get("profile_picture")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.root_path, "static", "uploads", filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            file.save(upload_path)
            current_user.profile_picture = filename

        if not username:
            errors["username"] = "Username cannot be empty"
        if not email:
            errors["email"] = "Email cannot be empty"

        if not errors:
            current_user.username = username
            current_user.email = email
            current_user.skills = skills
            current_user.bio = bio

        if current_password or new_password or confirm_password:
            if not check_password_hash(current_user.password_hash, current_password):
                errors["password"] = "Current password is incorrect"
            elif new_password != confirm_password:
                errors["password"] = "New passwords do not match"
            elif len(new_password) < 6:
                errors["password"] = "Password must be at least 6 characters long"
            else:
                current_user.password_hash = generate_password_hash(new_password)

        if not errors:
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(get_dashboard_url())
        else:
            for err in errors.values():
                flash(err, "danger")

    return render_template("edit_profile.html", user=current_user, errors=errors, dashboard_url=get_dashboard_url())


def get_dashboard_url():
    """ return to dashboard"""
    if current_user.role == "admin":
        return url_for("admin.dashboard")
    elif current_user.role == "volunteer":
        return url_for("volunteer.dashboard")
    else:
        return url_for("participant.dashboard")
