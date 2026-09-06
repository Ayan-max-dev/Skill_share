import os
from datetime import datetime
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Skill, Offer, Request, Session, Enrollment, RequestUpvote, Feedback, Lesson, Comment

from flask import jsonify


load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///skillshare.db"
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "fallback-only-for-local-dev")

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

def require_complete_profile(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.profile_complete:
            flash("Please complete your profile before doing that.")
            return redirect(url_for("edit_profile"))
        return f(*args, **kwargs)
    return decorated

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/add-user", methods=["GET", "POST"])
def add_user():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.")
            return redirect(url_for("add_user"))

        new_user = User(name=name, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("dashboard"))

    return render_template("add_user.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))

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
def view_users():
    all_users = User.query.all()
    return render_template("users.html", users=all_users)

@app.route("/explore")
def explore():
    category = request.args.get("category")
    format_filter = request.args.get("format")
    level_filter = request.args.get("level")
    search_query = request.args.get("q", "").strip()

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
    offers.sort(key=lambda o: o.confirmed_count, reverse=True)
    requests_list = requests_query.all()
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

@app.route("/requests/search-similar")
def search_similar_requests():
    query = request.args.get("q", "").strip()
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
            "id": r.id,
            "skill_name": r.skill.name,
            "student_name": r.student.name,
            "upvote_count": len(r.upvotes),
        }
        for r in matches
    ]
    return jsonify(results)

@app.route("/requests/new", methods=["GET", "POST"])
@login_required
def new_request():
    if request.method == "POST":
        skill_name = request.form["skill_name"].strip()
        category = request.form["category"]
        description = request.form.get("description", "").strip()
        preferred_time = request.form.get("preferred_time", "").strip()

        if not skill_name:
            flash("Skill is required.")
            return redirect(url_for("new_request"))

        skill = Skill.query.filter(db.func.lower(Skill.name) == skill_name.lower()).first()
        if not skill:
            skill = Skill(name=skill_name, category=category)
            db.session.add(skill)
            db.session.flush()

        new_req = Request(
            student_id=current_user.id,
            skill_id=skill.id,
            description=description,
            preferred_time=preferred_time,
        )
        db.session.add(new_req)
        db.session.commit()
        flash("Your request has been posted!")
        return redirect(url_for("explore"))

    return render_template("new_request.html")

@app.route("/offers/<int:offer_id>")
def offer_detail(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    return render_template("offer_detail.html", offer=offer)
@app.route("/offers/<int:offer_id>/schedule", methods=["GET", "POST"])
@login_required
@require_complete_profile
def schedule_session(offer_id):
    offer = Offer.query.get_or_404(offer_id)

    if offer.teacher_id != current_user.id:
        flash("Only the teacher who posted this offer can schedule a session.")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    if request.method == "POST":
        start_str = request.form["start_time"]
        end_str = request.form["end_time"]
        meeting_link = request.form.get("meeting_link", "").strip()

        start_time = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
        end_time = datetime.strptime(end_str, "%Y-%m-%dT%H:%M")

        if end_time <= start_time:
            flash("End time must be after start time.")
            return redirect(url_for("schedule_session", offer_id=offer.id))

        session = Session(
            offer_id=offer.id,
            start_time=start_time,
            end_time=end_time,
            meeting_link=meeting_link,
        )
        db.session.add(session)
        db.session.commit()
        flash("Session scheduled!")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    return render_template("schedule_session.html", offer=offer)

@app.route("/sessions/<int:session_id>/rsvp", methods=["POST"])
@login_required
@require_complete_profile
def rsvp_session(session_id):
    session = Session.query.get_or_404(session_id)
    offer = session.offer

    if offer.teacher_id == current_user.id:
        flash("You can't RSVP to your own session.")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    if request.form.get("consent") != "on":
        flash("You must acknowledge the recording notice to RSVP.")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    existing = Enrollment.query.filter_by(session_id=session.id, student_id=current_user.id).first()
    if existing:
        flash("You've already RSVP'd to this session.")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    confirmed_count = Enrollment.query.filter_by(session_id=session.id, status="confirmed").count()
    status = "confirmed" if confirmed_count < offer.max_attendees else "waitlisted"

    enrollment = Enrollment(session_id=session.id, student_id=current_user.id, status=status)
    db.session.add(enrollment)
    db.session.commit()

    if status == "confirmed":
        flash("You're confirmed! Check the session page for the meeting link.")
    else:
        flash("Session is full — you've been added to the waitlist.")

    return redirect(url_for("offer_detail", offer_id=offer.id))

@app.route("/profile")
@login_required
def my_profile():
    return redirect(url_for("view_profile", user_id=current_user.id))

@app.route("/profile/<int:user_id>")
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    courses_taught = Offer.query.filter_by(teacher_id=user.id).all()
    return render_template("profile.html", profile_user=user, courses_taught=courses_taught)

@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        current_user.bio = request.form.get("bio", "").strip()
        current_user.grade = request.form.get("grade", "").strip()
        current_user.courses_completed = request.form.get("courses_completed", "").strip()
        db.session.commit()
        flash("Profile updated!")
        return redirect(url_for("dashboard"))
    return render_template("edit_profile.html")

@app.route("/requests/<int:request_id>/upvote", methods=["POST"])
@login_required
def upvote_request(request_id):
    req = Request.query.get_or_404(request_id)

    if req.student_id == current_user.id:
        flash("You can't upvote your own request.")
        return redirect(url_for("explore"))

    existing = RequestUpvote.query.filter_by(request_id=req.id, user_id=current_user.id).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash("Upvote removed.")
    else:
        upvote = RequestUpvote(request_id=req.id, user_id=current_user.id)
        db.session.add(upvote)
        db.session.commit()
        flash("Upvoted!")

    return redirect(url_for("explore"))

@app.route("/sessions/<int:session_id>/feedback", methods=["GET", "POST"])
@login_required
def session_feedback(session_id):
    session = Session.query.get_or_404(session_id)
    offer = session.offer

    enrollment = Enrollment.query.filter_by(
        session_id=session.id, student_id=current_user.id, status="confirmed"
    ).first()
    if not enrollment:
        flash("You can only leave feedback for sessions you attended.")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    if enrollment.attended is False:
        flash("You were marked as not attending this session, so feedback isn't available.")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    if not session.has_ended:
        flash("This session hasn't ended yet.")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    existing = Feedback.query.filter_by(session_id=session.id, student_id=current_user.id).first()
    if existing:
        flash("You've already given feedback for this session.")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    if request.method == "POST":
        rating = request.form.get("rating", type=int)
        comment = request.form.get("comment", "").strip()

        if not rating or rating < 1 or rating > 5:
            flash("Please select a star rating.")
            return redirect(url_for("session_feedback", session_id=session.id))

        feedback = Feedback(session_id=session.id, student_id=current_user.id, rating=rating, comment=comment)
        db.session.add(feedback)
        db.session.commit()
        flash("Thanks for your feedback!")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    return render_template("session_feedback.html", session=session, offer=offer)

@app.route("/sessions/<int:session_id>/attendance", methods=["GET", "POST"])
@login_required
def mark_attendance(session_id):
    session = Session.query.get_or_404(session_id)
    offer = session.offer

    if offer.teacher_id != current_user.id:
        flash("Only the teacher can mark attendance.")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    if not session.has_ended:
        flash("You can mark attendance once the session has ended.")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    confirmed_enrollments = Enrollment.query.filter_by(session_id=session.id, status="confirmed").all()

    if request.method == "POST":
        for enrollment in confirmed_enrollments:
            # checkbox is only present in form data if it was checked
            enrollment.attended = request.form.get(f"attended_{enrollment.id}") == "on"
        db.session.commit()
        flash("Attendance updated!")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    return render_template("mark_attendance.html", session=session, offer=offer, enrollments=confirmed_enrollments)

@app.route("/sessions/<int:session_id>/recording", methods=["GET", "POST"])
@login_required
def add_recording(session_id):
    session = Session.query.get_or_404(session_id)
    offer = session.offer

    if offer.teacher_id != current_user.id:
        flash("Only the teacher can add the recording.")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    if not session.has_ended:
        flash("You can add the recording once the session has ended.")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    if request.method == "POST":
        url = request.form.get("recording_url", "").strip()
        if not url:
            flash("Please paste a recording link.")
            return redirect(url_for("add_recording", session_id=session.id))

        session.recording_url = url
        db.session.commit()
        flash("Recording added — thanks for keeping the class verified!")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    return render_template("add_recording.html", session=session, offer=offer)

#correct
@app.route("/offers/new", methods=["GET", "POST"])
@login_required
def new_offer():
    request_id = request.values.get("request_id", type=int)
    fulfilling_request = Request.query.get(request_id) if request_id else None
    offer_format = request.values.get("format", "live")

    if request.method == "POST":
        skill_name = request.form["skill_name"].strip()
        category = request.form["category"]
        title = request.form["title"].strip()
        description = request.form.get("description", "").strip()
        level = request.form["level"]
        format_choice = request.form.get("format", "live")
        max_attendees = request.form.get("max_attendees", 10)

        if not skill_name or not title:
            flash("Skill and title are required.")
            return redirect(url_for("new_offer"))

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
            max_attendees=int(max_attendees) if format_choice == "live" else 0,
            format=format_choice,
        )
        db.session.add(offer)

        if fulfilling_request:
            fulfilling_request.status = "fulfilled"

        db.session.commit()
        flash("Your offer has been posted!")

        if format_choice == "recorded":
            return redirect(url_for("manage_lessons", offer_id=offer.id))
        return redirect(url_for("explore"))

    return render_template("new_offer.html", fulfilling_request=fulfilling_request, offer_format=offer_format)

@app.route("/offers/<int:offer_id>/lessons", methods=["GET", "POST"])
@login_required
def manage_lessons(offer_id):
    offer = Offer.query.get_or_404(offer_id)

    if offer.teacher_id != current_user.id:
        flash("Only the teacher who posted this offer can manage lessons.")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    if offer.format != "recorded":
        flash("This offer isn't a recorded course.")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    if request.method == "POST":
        lesson_title = request.form.get("lesson_title", "").strip()
        video_url = request.form.get("video_url", "").strip()

        if not lesson_title or not video_url:
            flash("Lesson title and video link are required.")
            return redirect(url_for("manage_lessons", offer_id=offer.id))

        next_order = len(offer.lessons)
        lesson = Lesson(offer_id=offer.id, title=lesson_title, video_url=video_url, order=next_order)
        db.session.add(lesson)
        db.session.commit()
        flash("Lesson added!")
        return redirect(url_for("manage_lessons", offer_id=offer.id))

    sorted_lessons = sorted(offer.lessons, key=lambda l: l.order)
    return render_template("manage_lessons.html", offer=offer, lessons=sorted_lessons)

@app.route("/offers/<int:offer_id>/comments", methods=["POST"])
@login_required
def add_comment(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    content = request.form.get("content", "").strip()

    if not content:
        flash("Comment can't be empty.")
        return redirect(url_for("offer_detail", offer_id=offer.id))

    comment = Comment(offer_id=offer.id, user_id=current_user.id, content=content)
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for("offer_detail", offer_id=offer.id))

if __name__ == "__main__":
    app.run(debug=True)