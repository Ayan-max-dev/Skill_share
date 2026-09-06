from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    grade = db.Column(db.String(20), nullable=True)
    courses_completed = db.Column(db.Text, nullable=True)  # free text, e.g. "AP Bio, Algebra II, Spanish 3"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def profile_complete(self):
        return bool(self.grade and self.courses_completed)

    @property
    def average_teaching_rating(self):
        all_feedback = [
            feedback
            for offer in self.offers
            for session in offer.sessions
            for feedback in session.feedback
        ]
        if not all_feedback:
            return None
        return round(sum(feedback.rating for feedback in all_feedback) / len(all_feedback), 1)

    @property
    def total_ratings_count(self):
        return sum(
            len(session.feedback)
            for offer in self.offers
            for session in offer.sessions
        )
    @property
    def no_show_count(self):
        return Enrollment.query.filter_by(student_id=self.id, attended=False).count()

    @property
    def attended_count(self):
        return Enrollment.query.filter_by(student_id=self.id, attended=True).count()
    
    @property
    def skills_learned(self):
        confirmed_enrollments = Enrollment.query.filter_by(
            student_id=self.id, status="confirmed", attended=True
        ).all()
        seen = {}
        for enrollment in confirmed_enrollments:
            offer = enrollment.session.offer
            skill_name = offer.skill.name
            if skill_name not in seen:
                seen[skill_name] = {"skill": skill_name, "offer_title": offer.title, "date": enrollment.session.start_time}
        return list(seen.values())
    
    @property
    def sessions_taught_count(self):
        return sum(
            1
            for offer in self.offers
            for session in offer.sessions
            if any(e.status == "confirmed" and e.attended for e in session.enrollments)
        )

    @property
    def teaching_badges(self):
        count = self.sessions_taught_count
        badges = []
        if count >= 1:
            badges.append("First Class Taught")
        if count >= 3:
            badges.append("Regular Teacher")
        if count >= 5:
            badges.append("Master Teacher")
        return badges

    @property
    def learner_badges(self):
        return [f"Completed: {entry['skill']}" for entry in self.skills_learned]
    
class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # e.g. Technology, Music, Sports

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skill.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    level = db.Column(db.String(20), nullable=False)
    max_attendees = db.Column(db.Integer, default=10)
    status = db.Column(db.String(20), default="open")
    format = db.Column(db.String(20), default="live")  # "live" or "recorded"

    teacher = db.relationship("User", backref="offers")
    skill = db.relationship("Skill", backref="offers")

    @property
    def confirmed_count(self):
        return sum(1 for session in self.sessions for e in session.enrollments if e.status == "confirmed")

    @property
    def average_rating(self):
        all_feedback = [f for session in self.sessions for f in session.feedback]
        if not all_feedback:
            return None
        return round(sum(f.rating for f in all_feedback) / len(all_feedback), 1)


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer, db.ForeignKey("offer.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    video_url = db.Column(db.String(300), nullable=False)
    order = db.Column(db.Integer, default=0)  # controls playback/display order

    offer = db.relationship("Offer", backref="lessons")
        
class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skill.id"), nullable=False)
    description = db.Column(db.Text, nullable=True)
    preferred_time = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default="open")  # open / fulfilled

    student = db.relationship("User", backref="requests")
    skill = db.relationship("Skill", backref="requests")

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer, db.ForeignKey("offer.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    meeting_link = db.Column(db.String(300), nullable=True)
    recording_url = db.Column(db.String(300), nullable=True)

    offer = db.relationship("Offer", backref="sessions")

    RECORDING_GRACE_HOURS = 48

    @property
    def has_ended(self):
        return self.end_time < datetime.now()

    @property
    def recording_deadline(self):
        return self.end_time + timedelta(hours=self.RECORDING_GRACE_HOURS)

    @property
    def recording_status(self):
        if not self.has_ended:
            return "not_yet"
        if self.recording_url:
            return "uploaded"
        if datetime.now() <= self.recording_deadline:
            return "pending"
        return "overdue"

    # ... your existing thumbs/rating properties stay below
    @property
    def average_rating(self):
        if not self.feedback:
            return None
        return round(sum(f.rating for f in self.feedback) / len(self.feedback), 1)

    @property
    def rating_count(self):
        return len(self.feedback)


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(20), default="confirmed")  # confirmed / waitlisted
    attended = db.Column(db.Boolean, nullable=True)  # None = not marked yet, True/False once teacher marks it

    session = db.relationship("Session", backref="enrollments")
    student = db.relationship("User", backref="enrollments")
    
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 = thumbs down, 5 = thumbs up
    comment = db.Column(db.Text, nullable=True)

    __table_args__ = (db.UniqueConstraint("session_id", "student_id", name="unique_session_feedback"),)

    session = db.relationship("Session", backref="feedback")
    student = db.relationship("User", backref="feedback_given")
    
    
class RequestUpvote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("request.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    __table_args__ = (db.UniqueConstraint("request_id", "user_id", name="unique_request_upvote"),)

    request = db.relationship("Request", backref="upvotes")
    user = db.relationship("User", backref="request_upvotes")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer, db.ForeignKey("offer.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    offer = db.relationship("Offer", backref="comments")
    user = db.relationship("User", backref="comments")