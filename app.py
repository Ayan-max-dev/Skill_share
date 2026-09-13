from datetime import datetime
from functools import wraps
from urllib.parse import urlparse
import logging
from flask import Flask, abort, render_template, request, redirect, url_for, flash
from flask_login import  login_required, current_user
from models import db, User, Skill, Offer, Request, Session, Enrollment, RequestUpvote, Feedback, Lesson, Comment
from config import Config
from flask_migrate import Migrate
from flask import jsonify
from sqlalchemy.exc import IntegrityError
from auth.routes import auth_bp
from profiles.routes import profiles_bp
from offers.routes import offers_bp
from learning_requests.routes import requests_bp
from extensions import csrf, login_manager, limiter
from sessions.routes import sessions_bp
from sqlalchemy.orm import selectinload
from main.routes import main_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate = Migrate(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(profiles_bp)
    app.register_blueprint(offers_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(main_bp)

    login_manager.login_view = "auth.login"

    if not app.debug:
        logging.basicConfig(level=logging.INFO)

    return app

app = create_app()

ALLOWED_CATEGORIES = {"Academic", "Non-academic"}
ALLOWED_FORMATS = {"live", "recorded"}
ALLOWED_LEVELS = {"Beginner", "Intermediate", "Advanced"}



def positive_int(value, minimum=1, maximum=50):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return value if minimum <= value <= maximum else None


def valid_url(value, max_length=300):
    if not value or len(value) > max_length:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

def require_complete_profile(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.profile_complete:
            flash("Please complete your profile before doing that.")
            return redirect(url_for("profiles.edit_profile"))
        return f(*args, **kwargs)
    return decorated

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.errorhandler(403)
def forbidden(error):
    return render_template("403.html"), 403


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=False)