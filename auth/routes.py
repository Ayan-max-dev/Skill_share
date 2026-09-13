from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from extensions import limiter
from models import User, db


auth_bp = Blueprint("auth", __name__)


def bounded_text(value, max_length):
    value = (value or "").strip()
    return value if len(value) <= max_length else None


@auth_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@auth_bp.route("/add-user", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def add_user():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = bounded_text(request.form.get("name"), 100)
        email = bounded_text(request.form.get("email"), 120)
        password = request.form.get("password", "")

        if not name or not email or "@" not in email or not 8 <= len(password) <= 128:
            flash("Enter a valid name, email, and password (8–128 characters).")
            return redirect(url_for("auth.add_user"))

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.")
            return redirect(url_for("auth.add_user"))

        new_user = User(name=name, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("dashboard"))

    return render_template("add_user.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = bounded_text(request.form.get("email"), 120)
        password = request.form.get("password", "")
        if not email or not password or len(password) > 128:
            flash("Enter your email and password.")
            return redirect(url_for("auth.login"))
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.home"))
