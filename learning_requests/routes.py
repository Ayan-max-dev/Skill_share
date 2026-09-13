from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from models import Request, RequestUpvote, Skill, db


requests_bp = Blueprint("requests", __name__)

ALLOWED_CATEGORIES = {"Academic", "Non-academic"}


def bounded_text(value, max_length):
    value = (value or "").strip()
    return value if len(value) <= max_length else None


@requests_bp.route("/requests/search-similar")
@login_required
def search_similar_requests():
    query = bounded_text(request.args.get("q", ""), 100) or ""
    if len(query) < 2:
        return jsonify([])

    matches = (
        Request.query
        .join(Skill)
        .filter(Request.status == "open")
        .filter(Skill.name.ilike(f"%{query}%"))
        .limit(5)
        .all()
    )

    results = [
        {
            "id": learning_request.id,
            "skill_name": learning_request.skill.name,
            "student_name": learning_request.student.name,
            "upvote_count": len(learning_request.upvotes),
        }
        for learning_request in matches
    ]
    return jsonify(results)


@requests_bp.route("/requests/new", methods=["GET", "POST"])
@login_required
def new_request():
    if request.method == "POST":
        skill_name = bounded_text(request.form.get("skill_name"), 100)
        category = request.form.get("category")
        description = bounded_text(request.form.get("description"), 2000)
        preferred_time = bounded_text(request.form.get("preferred_time"), 100)

        if not skill_name or category not in ALLOWED_CATEGORIES or description is None or preferred_time is None:
            flash("Enter a valid skill, category, description, and preferred time.")
            return redirect(url_for("requests.new_request"))

        skill = Skill.query.filter(db.func.lower(Skill.name) == skill_name.lower()).first()
        if not skill:
            skill = Skill(name=skill_name, category=category)
            db.session.add(skill)
            db.session.flush()

        new_learning_request = Request(
            student_id=current_user.id,
            skill_id=skill.id,
            description=description,
            preferred_time=preferred_time,
        )
        db.session.add(new_learning_request)
        db.session.commit()
        flash("Your request has been posted!")
        return redirect(url_for("main.explore"))

    return render_template("new_request.html")


@requests_bp.route("/requests/<int:request_id>/upvote", methods=["POST"])
@login_required
def upvote_request(request_id):
    learning_request = Request.query.get_or_404(request_id)

    if learning_request.student_id == current_user.id:
        flash("You can't upvote your own request.")
        return redirect(url_for("main.explore"))

    existing = RequestUpvote.query.filter_by(
        request_id=learning_request.id,
        user_id=current_user.id,
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash("Upvote removed.")
    else:
        upvote = RequestUpvote(
            request_id=learning_request.id,
            user_id=current_user.id,
        )
        db.session.add(upvote)
        db.session.commit()
        flash("Upvoted!")

    return redirect(url_for("main.explore"))


@requests_bp.route("/requests/<int:request_id>/delete", methods=["POST"])
@login_required
def delete_request(request_id):
    learning_request = Request.query.get_or_404(request_id)

    if current_user.id != learning_request.student_id:
        abort(403)

    try:
        for upvote in learning_request.upvotes:
            db.session.delete(upvote)
        db.session.delete(learning_request)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("This request could not be deleted safely.")
        return redirect(url_for("main.explore"))

    flash("Request deleted.")
    return redirect(url_for("main.explore"))
