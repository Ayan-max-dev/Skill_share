from datetime import datetime
from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from models import Enrollment, Feedback, Offer, Session, db


sessions_bp = Blueprint("sessions", __name__)


def bounded_text(value, max_length):
    value = (value or "").strip()
    return value if len(value) <= max_length else None


def valid_url(value, max_length=300):
    if not value or len(value) > max_length:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


@sessions_bp.route("/offers/<int:offer_id>/schedule", methods=["GET", "POST"])
@login_required
def schedule_session(offer_id):
    offer = Offer.query.get_or_404(offer_id)

    if not current_user.profile_complete:
        flash("Please complete your profile before doing that.")
        return redirect(url_for("profiles.edit_profile"))

    if offer.teacher_id != current_user.id:
        flash("Only the teacher who posted this offer can schedule a session.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if request.method == "POST":
        start_str = bounded_text(request.form.get("start_time"), 16)
        end_str = bounded_text(request.form.get("end_time"), 16)
        meeting_link = bounded_text(request.form.get("meeting_link"), 300)

        if not start_str or not end_str or meeting_link is None or (meeting_link and not valid_url(meeting_link)):
            flash("Enter valid start, end, and meeting link values.")
            return redirect(url_for("sessions.schedule_session", offer_id=offer.id))

        try:
            start_time = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
            end_time = datetime.strptime(end_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Enter valid start and end times.")
            return redirect(url_for("sessions.schedule_session", offer_id=offer.id))

        if end_time <= start_time:
            flash("End time must be after start time.")
            return redirect(url_for("sessions.schedule_session", offer_id=offer.id))

        new_session = Session(
            offer_id=offer.id,
            start_time=start_time,
            end_time=end_time,
            meeting_link=meeting_link,
        )
        db.session.add(new_session)
        db.session.commit()
        flash("Session scheduled!")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    return render_template("schedule_session.html", offer=offer)


@sessions_bp.route("/sessions/<int:session_id>/rsvp", methods=["POST"])
@login_required
def rsvp_session(session_id):
    target_session = Session.query.get_or_404(session_id)
    offer = target_session.offer

    if not current_user.profile_complete:
        flash("Please complete your profile before doing that.")
        return redirect(url_for("profiles.edit_profile"))

    if target_session.is_cancelled:
        flash("This session has been cancelled.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if offer.teacher_id == current_user.id:
        flash("You can't RSVP to your own session.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if request.form.get("consent") != "on":
        flash("You must acknowledge the recording notice to RSVP.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    existing = Enrollment.query.filter_by(session_id=target_session.id, student_id=current_user.id).first()
    if existing:
        flash("You've already RSVP'd to this session.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    confirmed_count = Enrollment.query.filter_by(session_id=target_session.id, status="confirmed").count()
    status = "confirmed" if confirmed_count < offer.max_attendees else "waitlisted"

    enrollment = Enrollment(
        session_id=target_session.id,
        student_id=current_user.id,
        status=status,
    )
    db.session.add(enrollment)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("You've already RSVP'd to this session.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if status == "confirmed":
        flash("You're confirmed! Check the session page for the meeting link.")
    else:
        flash("Session is full — you've been added to the waitlist.")

    return redirect(url_for("offers.offer_detail", offer_id=offer.id))


@sessions_bp.route("/sessions/<int:session_id>/feedback", methods=["GET", "POST"])
@login_required
def session_feedback(session_id):
    target_session = Session.query.get_or_404(session_id)
    offer = target_session.offer

    enrollment = Enrollment.query.filter_by(
        session_id=target_session.id, student_id=current_user.id, status="confirmed"
    ).first()
    if not enrollment:
        flash("You can only leave feedback for sessions you attended.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if enrollment.attended is False:
        flash("You were marked as not attending this session, so feedback isn't available.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if not target_session.has_ended:
        flash("This session hasn't ended yet.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    existing = Feedback.query.filter_by(session_id=target_session.id, student_id=current_user.id).first()
    if existing:
        flash("You've already given feedback for this session.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if request.method == "POST":
        rating = request.form.get("rating", type=int)
        comment = bounded_text(request.form.get("comment"), 2000)

        if rating is None or not 1 <= rating <= 5 or comment is None:
            flash("Select a rating from 1 to 5 and keep the comment within 2,000 characters.")
            return redirect(url_for("sessions.session_feedback", session_id=target_session.id))

        feedback = Feedback(session_id=target_session.id, student_id=current_user.id, rating=rating, comment=comment)
        db.session.add(feedback)
        db.session.commit()
        flash("Thanks for your feedback!")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    return render_template("session_feedback.html", session=target_session, offer=offer)


@sessions_bp.route("/sessions/<int:session_id>/attendance", methods=["GET", "POST"])
@login_required
def mark_attendance(session_id):
    target_session = Session.query.get_or_404(session_id)
    offer = target_session.offer

    if target_session.is_cancelled:
        flash("This session has been cancelled.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if offer.teacher_id != current_user.id:
        flash("Only the teacher can mark attendance.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if not target_session.has_ended:
        flash("You can mark attendance once the session has ended.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    confirmed_enrollments = Enrollment.query.filter_by(session_id=target_session.id, status="confirmed").all()

    if request.method == "POST":
        for enrollment in confirmed_enrollments:
            enrollment.attended = request.form.get(f"attended_{enrollment.id}") == "on"
        db.session.commit()
        flash("Attendance updated!")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    return render_template(
        "mark_attendance.html", session=target_session, offer=offer, enrollments=confirmed_enrollments
    )


@sessions_bp.route("/sessions/<int:session_id>/recording", methods=["GET", "POST"])
@login_required
def add_recording(session_id):
    target_session = Session.query.get_or_404(session_id)
    offer = target_session.offer

    if target_session.is_cancelled:
        flash("This session has been cancelled.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if offer.teacher_id != current_user.id:
        flash("Only the teacher can add the recording.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if not target_session.has_ended:
        flash("You can add the recording once the session has ended.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if request.method == "POST":
        url = bounded_text(request.form.get("recording_url"), 300)
        if not url or not valid_url(url):
            flash("Please paste a valid HTTP or HTTPS recording link.")
            return redirect(url_for("sessions.add_recording", session_id=target_session.id))

        target_session.recording_url = url
        db.session.commit()
        flash("Recording added — thanks for keeping the class verified!")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    return render_template("add_recording.html", session=target_session, offer=offer)


@sessions_bp.route("/sessions/<int:session_id>/cancel", methods=["GET", "POST"])
@login_required
def cancel_session(session_id):
    target_session = Session.query.get_or_404(session_id)
    offer = target_session.offer

    if offer.teacher_id != current_user.id:
        flash("Only the teacher can cancel this session.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if target_session.has_ended:
        flash("You can't cancel a session that's already happened.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if target_session.is_cancelled:
        flash("This session is already cancelled.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    if request.method == "POST":
        reason = bounded_text(request.form.get("reason"), 1000)
        if not reason:
            flash("Please provide a reason no longer than 1,000 characters.")
            return redirect(url_for("sessions.cancel_session", session_id=target_session.id))

        target_session.status = "cancelled"
        target_session.cancelled_reason = reason
        db.session.commit()
        flash("Session cancelled. Attendees will see the update.")
        return redirect(url_for("offers.offer_detail", offer_id=offer.id))

    return render_template("cancel_session.html", session=target_session, offer=offer)