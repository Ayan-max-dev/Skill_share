# seed.py
from app import app, db
from models import User, Skill, Offer, Request, Session, Enrollment, RequestUpvote, Feedback, Lesson
from datetime import datetime, timedelta

with app.app_context():
    # Wipe and recreate tables so seeding is always a clean slate
    db.drop_all()
    db.create_all()

    # --- Users ---
    john = User(name="John Smith", email="john@school.edu", grade="11th Grade",
                courses_completed="Algebra II, Chemistry, Spanish 3",
                bio="I love cubing and teaching math.")
    john.set_password("password123")

    priya = User(name="Priya Patel", email="priya@school.edu", grade="12th Grade",
                 courses_completed="AP Bio, Calculus BC",
                 bio="Happy to help with science and chess.")
    priya.set_password("password123")

    sam = User(name="Sam Lee", email="sam@school.edu", grade="9th Grade",
               courses_completed="Geometry, World History",
               bio="Just here to learn stuff.")
    sam.set_password("password123")

    # Deliberately incomplete profile — use this account to test the profile gate
    alex = User(name="Alex Kim", email="alex@school.edu")
    alex.set_password("password123")

    db.session.add_all([john, priya, sam, alex])
    db.session.flush()

    # --- Skills ---
    rubiks = Skill(name="Rubik's Cube", category="Non-academic")
    chess = Skill(name="Chess", category="Non-academic")
    calculus = Skill(name="Calculus", category="Academic")
    guitar = Skill(name="Guitar", category="Non-academic")

    db.session.add_all([rubiks, chess, calculus, guitar])
    db.session.flush()

    # --- Offers (live) ---
    offer1 = Offer(teacher_id=john.id, skill_id=rubiks.id,
                    title="Intro to Speedcubing", description="Learn the basics of solving a 3x3.",
                    level="Beginner", max_attendees=5, format="live")
    offer2 = Offer(teacher_id=priya.id, skill_id=calculus.id,
                    title="Calc BC Review Session", description="Covering derivatives and integrals.",
                    level="Advanced", max_attendees=8, format="live")

    # --- Offer (recorded, multi-lesson course) ---
    offer3 = Offer(teacher_id=priya.id, skill_id=guitar.id,
                    title="Beginner Guitar in 3 Parts", description="A self-paced intro to guitar basics.",
                    level="Beginner", max_attendees=0, format="recorded")

    db.session.add_all([offer1, offer2, offer3])
    db.session.flush()

    # --- Lessons for the recorded course ---
    lesson1 = Lesson(offer_id=offer3.id, title="Holding the guitar & tuning", video_url="https://youtube.com/watch?v=example1", order=0)
    lesson2 = Lesson(offer_id=offer3.id, title="Your first chords", video_url="https://youtube.com/watch?v=example2", order=1)
    lesson3 = Lesson(offer_id=offer3.id, title="Simple strumming patterns", video_url="https://youtube.com/watch?v=example3", order=2)
    db.session.add_all([lesson1, lesson2, lesson3])

    # --- Requests ---
    req1 = Request(student_id=sam.id, skill_id=chess.id,
                    description="Want to learn chess openings.", preferred_time="Weekday afternoons")

    db.session.add(req1)
    db.session.flush()

    # --- Upvotes on Sam's chess request ---
    upvote1 = RequestUpvote(request_id=req1.id, user_id=john.id)
    upvote2 = RequestUpvote(request_id=req1.id, user_id=priya.id)
    db.session.add_all([upvote1, upvote2])

    # --- Upcoming session (for testing RSVP flow) ---
    upcoming_session = Session(
        offer_id=offer1.id,
        start_time=datetime.now() + timedelta(days=2, hours=3),
        end_time=datetime.now() + timedelta(days=2, hours=4),
        meeting_link="https://zoom.us/j/example123",
    )
    db.session.add(upcoming_session)
    db.session.flush()

    # Priya RSVPs to John's upcoming session
    enrollment1 = Enrollment(session_id=upcoming_session.id, student_id=priya.id, status="confirmed")
    db.session.add(enrollment1)

    # --- Already-ended session, recording NOT yet added (tests the "overdue" reminder) ---
    past_session = Session(
        offer_id=offer1.id,
        start_time=datetime.now() - timedelta(days=3, hours=2),
        end_time=datetime.now() - timedelta(days=3, hours=1),
        meeting_link="https://zoom.us/j/example456",
        recording_url=None,
    )
    db.session.add(past_session)
    db.session.flush()

    # Sam attended and left feedback; Priya no-showed; Alex attended but hasn't left feedback
    enrollment2 = Enrollment(session_id=past_session.id, student_id=sam.id, status="confirmed", attended=True)
    enrollment3 = Enrollment(session_id=past_session.id, student_id=priya.id, status="confirmed", attended=False)
    enrollment4 = Enrollment(session_id=past_session.id, student_id=alex.id, status="confirmed", attended=True)
    db.session.add_all([enrollment2, enrollment3, enrollment4])
    db.session.flush()

    feedback1 = Feedback(session_id=past_session.id, student_id=sam.id, rating=5,
                          comment="Really clear explanation, learned a lot!")
    db.session.add(feedback1)

    db.session.commit()
    print("Database seeded!")
    print("Test accounts (all passwords: password123):")
    print("  john@school.edu   - teaches live offers; past session recording is OVERDUE (test the dashboard reminder)")
    print("  priya@school.edu  - teaches Calc BC (live) AND 'Beginner Guitar in 3 Parts' (recorded, 3 lessons already added)")
    print("  sam@school.edu    - attended past session, left 5-star feedback")
    print("  alex@school.edu   - profile INCOMPLETE, use to test the profile gate")