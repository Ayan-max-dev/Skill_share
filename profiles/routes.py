from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models import Offer, User, db


profiles_bp = Blueprint("profiles", __name__)


def bounded_text(value, max_length):
    value = (value or "").strip()
    return value if len(value) <= max_length else None


@profiles_bp.route("/profile")
@login_required
def my_profile():
    return redirect(url_for("profiles.view_profile", user_id=current_user.id))


@profiles_bp.route("/profile/<int:user_id>")
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    courses_taught = Offer.query.filter_by(teacher_id=user.id).all()
    return render_template("profile.html", profile_user=user, courses_taught=courses_taught)


@profiles_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        bio = bounded_text(request.form.get("bio"), 2000)
        grade = bounded_text(request.form.get("grade"), 20)
        courses_completed = bounded_text(request.form.get("courses_completed"), 1000)
        if not grade or not courses_completed or bio is None:
            flash("Enter a valid grade, courses list, and bio.")
            return redirect(url_for("profiles.edit_profile"))

        current_user.bio = bio
        current_user.grade = grade
        current_user.courses_completed = courses_completed
        db.session.commit()
        flash("Profile updated!")
        return redirect(url_for("dashboard"))
    return render_template("edit_profile.html")
