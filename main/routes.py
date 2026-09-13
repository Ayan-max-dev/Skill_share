from flask import Blueprint, app, render_template, request
from flask_login import login_required, current_user
from sqlalchemy.orm import selectinload
from models import Offer, Request, Enrollment, Skill, User, db

main_bp = Blueprint("main", __name__)

ALLOWED_CATEGORIES = {"Academic", "Non-academic"}
ALLOWED_FORMATS = {"live", "recorded"}
ALLOWED_LEVELS = {"Beginner", "Intermediate", "Advanced"}

# ... dashboard, explore, view_users, offer_relevance_score, request_relevance_score, bounded_text all move here
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


@main_bp.route("/dashboard")
@login_required
def dashboard():
    my_offers = (
    Offer.query
    .filter_by(teacher_id=current_user.id)
    .options(selectinload(Offer.sessions))
    .all()
    )
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



@main_bp.route("/explore")
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


@main_bp.route("/users")
@login_required
def view_users():
    all_users = User.query.all()
    return render_template("users.html", users=all_users)