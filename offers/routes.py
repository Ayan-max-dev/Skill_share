from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from models import Comment, Lesson, Offer, Request, Skill, db


offers_bp = Blueprint("offers", __name__)

ALLOWED_CATEGORIES = {"Academic", "Non-academic"}
ALLOWED_FORMATS = {"live", "recorded"}
ALLOWED_LEVELS = {"Beginner", "Intermediate", "Advanced"}


def bounded_text(value, max_length):
    value = (value or "").strip()
    return value if len(value) <= max_length else None


def positive_int(value, minimum=1, maximum=50):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return value if minimum <= value <= maximum else None


def valid_url(value, max_length=300):
    from urllib.parse import urlparse

    if not value or len(value) > max_length:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


@offers_bp.route("/offers/<int:offer_id>")
def offer_detail(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    return render_template("offer_detail.html", offer=offer)


@offers_bp.route("/offers/<int:offer_id>/delete", methods=["POST"])
@login_required
def delete_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)

    if current_user.id != offer.teacher_id:
        abort(403)

    if offer.sessions:
        flash("Offers with session history cannot be deleted.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    try:
        for lesson in offer.lessons:
            db.session.delete(lesson)
        for comment in offer.comments:
            db.session.delete(comment)
        db.session.delete(offer)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("This offer could not be deleted safely.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    flash("Offer deleted.")
    return redirect(url_for("main.explore"))


@offers_bp.route("/offers/new", methods=["GET", "POST"])
@login_required
def new_offer():
    request_id = request.values.get("request_id", type=int)
    fulfilling_request = Request.query.get(request_id) if request_id else None
    offer_format = request.values.get("format", "live")
    if offer_format not in ALLOWED_FORMATS:
        offer_format = "live"

    if request.method == "POST":
        skill_name = bounded_text(request.form.get("skill_name"), 100)
        category = request.form.get("category")
        title = bounded_text(request.form.get("title"), 150)
        description = bounded_text(request.form.get("description"), 2000)
        level = request.form.get("level")
        format_choice = request.form.get("format", "live")
        max_attendees = positive_int(request.form.get("max_attendees", 10))

        if (not skill_name or category not in ALLOWED_CATEGORIES or not title or
                description is None or level not in ALLOWED_LEVELS or
                format_choice not in ALLOWED_FORMATS or max_attendees is None):
            flash("Enter valid offer details, level, format, and attendee limit.")
            return redirect(url_for("offers.new_offer"))

        skill = Skill.query.filter(db.func.lower(Skill.name) == skill_name.lower()).first()
        if not skill:
            skill = Skill(name=skill_name, category=category)
            db.session.add(skill)
            db.session.flush()

        offer = Offer(
            teacher_id=current_user.id,
            skill_id=skill.id,
            title=title,
            description=description,
            level=level,
            max_attendees=max_attendees if format_choice == "live" else 0,
            format=format_choice,
        )
        db.session.add(offer)

        if fulfilling_request:
            fulfilling_request.status = "fulfilled"

        db.session.commit()
        flash("Your offer has been posted!")

        if format_choice == "recorded":
            return redirect(url_for("offers.manage_lessons", offer_id=offer.id))
        return redirect(url_for("main.explore"))

    return render_template("new_offer.html", fulfilling_request=fulfilling_request, offer_format=offer_format)


@offers_bp.route("/offers/<int:offer_id>/lessons", methods=["GET", "POST"])
@login_required
def manage_lessons(offer_id):
    offer = Offer.query.get_or_404(offer_id)

    if offer.teacher_id != current_user.id:
        flash("Only the teacher who posted this offer can manage lessons.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if offer.format != "recorded":
        flash("This offer isn't a recorded course.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if request.method == "POST":
        lesson_title = bounded_text(request.form.get("lesson_title"), 150)
        video_url = bounded_text(request.form.get("video_url"), 300)

        if not lesson_title or not video_url or not valid_url(video_url):
            flash("Enter a lesson title and valid HTTP or HTTPS video link.")
            return redirect(url_for("offers.manage_lessons", offer_id=offer.id))

        next_order = len(offer.lessons)
        lesson = Lesson(offer_id=offer.id, title=lesson_title, video_url=video_url, order=next_order)
        db.session.add(lesson)
        db.session.commit()
        flash("Lesson added!")
        return redirect(url_for("offers.manage_lessons", offer_id=offer.id))

    sorted_lessons = sorted(offer.lessons, key=lambda l: l.order)
    return render_template("manage_lessons.html", offer=offer, lessons=sorted_lessons)


@offers_bp.route("/offers/<int:offer_id>/comments", methods=["POST"])
@login_required
def add_comment(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    content = bounded_text(request.form.get("content"), 2000)

    if not content:
        flash("Comment can't be empty or longer than 2,000 characters.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    comment = Comment(offer_id=offer.id, user_id=current_user.id, content=content)
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for("offers.offer_detail", offer_id=offer.id))


@offers_bp.route("/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if current_user.id != comment.user_id:
        abort(403)

    offer_id = comment.offer_id
    try:
        db.session.delete(comment)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("This comment could not be deleted safely.")
        return redirect(url_for("offers.offer_detail", offer_id=offer_id))

    flash("Comment deleted.")
    return redirect(url_for("offers.offer_detail", offer_id=offer_id))


@offers_bp.route("/lessons/<int:lesson_id>/delete", methods=["POST"])
@login_required
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    offer = lesson.offer

    if current_user.id != offer.teacher_id:
        abort(403)

    try:
        db.session.delete(lesson)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("This lesson could not be deleted safely.")
        return redirect(url_for("offers.manage_lessons", offer_id=offer.id))

    flash("Lesson deleted.")
    return redirect(url_for("offers.manage_lessons", offer_id=offer.id))
