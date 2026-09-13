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


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

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
    login_manager.login_view = "auth.login"

    if not app.debug:
        logging.basicConfig(level=logging.INFO)

    return app

app = create_app()

ALLOWED_CATEGORIES = {"Academic", "Non-academic"}
ALLOWED_FORMATS = {"live", "recorded"}
ALLOWED_LEVELS = {"Beginner", "Intermediate", "Advanced"}



def bounded_text(value, max_length):
    value = (value or "").strip()
    return value if len(value) <= max_length else None

def offer_relevance_score(offer, query):
    query = query.lower()
    title = offer.title.lower()
    description = (offer.description or "").lower()
    skill_name = offer.skill.name.lower()

    score = 0

    if query == skill_name or query in skill_name:
        score += 100
    if title.startswith(query):
        score += 70
    elif query in title:
        score += 40
    if query in description:
        score += 15

    return score

def request_relevance_score(req, query):
    query = query.lower()
    description = (req.description or "").lower()
    skill_name = req.skill.name.lower()

    score = 0

    if query == skill_name or query in skill_name:
        score += 100
    if query in description:
        score += 15

    return score


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


@app.route("/dashboard")
@login_required
def dashboard():
    my_offers = Offer.query.filter_by(teacher_id=current_user.id).all()
    my_requests = Request.query.filter_by(student_id=current_user.id).all()
    my_enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()

    my_sessions = [s for offer in my_offers for s in offer.sessions]
    sessions_needing_recording = [s for s in my_sessions if s.recording_status in ("pending", "overdue")]

    return render_template(
        "dashboard.html",
        my_offers=my_offers,
        my_requests=my_requests,
        my_enrollments=my_enrollments,
        sessions_needing_recording=sessions_needing_recording,
    )

@app.route("/users")
@login_required
def view_users():
    all_users = User.query.all()
    return render_template("users.html", users=all_users)

@app.route("/explore")
def explore():
    category = request.args.get("category")
    format_filter = request.args.get("format")
    level_filter = request.args.get("level")
    search_query = bounded_text(request.args.get("q", ""), 100) or ""

    if category not in ALLOWED_CATEGORIES:
        category = None
    if format_filter not in ALLOWED_FORMATS:
        format_filter = None
    if level_filter not in ALLOWED_LEVELS:
        level_filter = None

    offers_query = Offer.query.join(Skill).filter(Offer.status == "open")
    requests_query = Request.query.join(Skill).filter(Request.status == "open")

    if category in ("Academic", "Non-academic"):
        offers_query = offers_query.filter(Skill.category == category)
        requests_query = requests_query.filter(Skill.category == category)

    if format_filter in ("live", "recorded"):
        offers_query = offers_query.filter(Offer.format == format_filter)

    if level_filter in ("Beginner", "Intermediate", "Advanced"):
        offers_query = offers_query.filter(Offer.level == level_filter)

    if search_query:
        like_pattern = f"%{search_query}%"
        offers_query = offers_query.filter(
            db.or_(
                Offer.title.ilike(like_pattern),
                Offer.description.ilike(like_pattern),
                Skill.name.ilike(like_pattern),
            )
        )
        requests_query = requests_query.filter(
            db.or_(
                Request.description.ilike(like_pattern),
                Skill.name.ilike(like_pattern),
            )
        )

    offers = offers_query.all()
    if search_query:
        offers.sort(key=lambda o: offer_relevance_score(o, search_query), reverse=True)
    else:
        offers.sort(key=lambda o: o.confirmed_count, reverse=True)
    requests_list = requests_query.all()
    if search_query:
        requests_list.sort(key=lambda r: request_relevance_score(r, search_query), reverse=True)
    else:
        requests_list.sort(key=lambda r: len(r.upvotes), reverse=True)

    return render_template(
        "explore.html",
        offers=offers,
        requests=requests_list,
        selected_category=category,
        selected_format=format_filter,
        selected_level=level_filter,
        search_query=search_query,
    )


@app.errorhandler(403)
def forbidden(error):
    return render_template("403.html"), 403


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=False)