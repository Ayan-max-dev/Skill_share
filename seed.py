from app import app, db
from models import (
    User, Skill, Offer, Request, Session, Enrollment,
    RequestUpvote, Feedback, Lesson, Comment
)
from datetime import datetime, timedelta


with app.app_context():
    # Wipe and recreate tables so seeding is always a clean slate
    db.drop_all()
    db.create_all()

    now = datetime.now()

    # ============================================================
    # USERS
    # ============================================================

    john = User(
        name="John Smith",
        email="john@school.edu",
        grade="11th Grade",
        courses_completed="Algebra II, Chemistry, Spanish 3",
        bio="I love cubing, solving puzzles, and teaching math."
    )
    john.set_password("password123")

    priya = User(
        name="Priya Patel",
        email="priya@school.edu",
        grade="12th Grade",
        courses_completed="AP Biology, Calculus BC, Physics",
        bio="Happy to help with science, chess, and music."
    )
    priya.set_password("password123")

    sam = User(
        name="Sam Lee",
        email="sam@school.edu",
        grade="9th Grade",
        courses_completed="Geometry, World History, Computer Science",
        bio="Curious about pretty much everything. Currently learning chess."
    )
    sam.set_password("password123")

    alex = User(
        name="Alex Kim",
        email="alex@school.edu",
        grade="10th Grade",
        courses_completed="Biology, Geometry, Computer Science",
        bio="Interested in technology, design, and photography."
    )
    alex.set_password("password123")

    maya = User(
        name="Maya Rodriguez",
        email="maya@school.edu",
        grade="11th Grade",
        courses_completed="English Literature, Art, Psychology",
        bio="Writer, artist, and occasional guitar player."
    )
    maya.set_password("password123")

    daniel = User(
        name="Daniel Chen",
        email="daniel@school.edu",
        grade="10th Grade",
        courses_completed="Computer Science, Algebra II, Physics",
        bio="I enjoy coding and helping people get started with Python."
    )
    daniel.set_password("password123")

    sara = User(
        name="Sara Ahmed",
        email="sara@school.edu",
        grade="12th Grade",
        courses_completed="Economics, Statistics, Business",
        bio="Interested in public speaking, entrepreneurship, and debate."
    )
    sara.set_password("password123")

    # Deliberately incomplete profile for testing the profile gate
    incomplete = User(
        name="Alex Test",
        email="incomplete@school.edu"
    )
    incomplete.set_password("password123")

    db.session.add_all([
        john, priya, sam, alex,
        maya, daniel, sara, incomplete
    ])
    db.session.flush()

    # ============================================================
    # SKILLS
    # ============================================================

    rubiks = Skill(name="Rubik's Cube", category="Non-academic")
    chess = Skill(name="Chess", category="Non-academic")
    calculus = Skill(name="Calculus", category="Academic")
    guitar = Skill(name="Guitar", category="Non-academic")
    python = Skill(name="Python Programming", category="Technology")
    public_speaking = Skill(name="Public Speaking", category="Communication")
    photography = Skill(name="Photography", category="Creative")
    debate = Skill(name="Debate", category="Communication")
    study_skills = Skill(name="Study Skills", category="Academic")
    graphic_design = Skill(name="Graphic Design", category="Creative")

    db.session.add_all([
        rubiks,
        chess,
        calculus,
        guitar,
        python,
        public_speaking,
        photography,
        debate,
        study_skills,
        graphic_design
    ])
    db.session.flush()

    # ============================================================
    # OFFERS
    # ============================================================

    offer1 = Offer(
        teacher_id=john.id,
        skill_id=rubiks.id,
        title="Intro to Speedcubing",
        description="Learn the basics of solving a 3x3 Rubik's Cube and improve your solving speed.",
        level="Beginner",
        max_attendees=5,
        format="live"
    )

    offer2 = Offer(
        teacher_id=priya.id,
        skill_id=calculus.id,
        title="Calculus BC Review",
        description="A focused review of derivatives, integrals, and common exam problems.",
        level="Advanced",
        max_attendees=8,
        format="live"
    )

    offer3 = Offer(
        teacher_id=priya.id,
        skill_id=guitar.id,
        title="Beginner Guitar in 3 Parts",
        description="A self-paced introduction to guitar basics, chords, and simple strumming.",
        level="Beginner",
        max_attendees=0,
        format="recorded"
    )

    offer4 = Offer(
        teacher_id=daniel.id,
        skill_id=python.id,
        title="Python from Zero",
        description="Learn Python fundamentals through small practical programs.",
        level="Beginner",
        max_attendees=10,
        format="live"
    )

    offer5 = Offer(
        teacher_id=sara.id,
        skill_id=public_speaking.id,
        title="Speak With Confidence",
        description="Practical techniques for speaking clearly and confidently in front of a group.",
        level="Intermediate",
        max_attendees=12,
        format="live"
    )

    offer6 = Offer(
        teacher_id=maya.id,
        skill_id=photography.id,
        title="Photography Basics",
        description="Learn composition, framing, lighting, and how to take better photos with your phone.",
        level="Beginner",
        max_attendees=8,
        format="live"
    )

    offer7 = Offer(
        teacher_id=sara.id,
        skill_id=debate.id,
        title="Debate Fundamentals",
        description="Learn how to structure arguments, respond to counterarguments, and think on your feet.",
        level="Intermediate",
        max_attendees=10,
        format="live"
    )

    offer8 = Offer(
        teacher_id=alex.id,
        skill_id=graphic_design.id,
        title="Design Your First Poster",
        description="Learn basic layout, typography, and visual hierarchy using beginner-friendly tools.",
        level="Beginner",
        max_attendees=6,
        format="live"
    )

    db.session.add_all([
        offer1, offer2, offer3, offer4,
        offer5, offer6, offer7, offer8
    ])
    db.session.flush()

    # ============================================================
    # RECORDED COURSE LESSONS
    # ============================================================

    lesson1 = Lesson(
        offer_id=offer3.id,
        title="Holding the Guitar & Tuning",
        video_url="https://youtube.com/watch?v=example1",
        order=0
    )

    lesson2 = Lesson(
        offer_id=offer3.id,
        title="Your First Chords",
        video_url="https://youtube.com/watch?v=example2",
        order=1
    )

    lesson3 = Lesson(
        offer_id=offer3.id,
        title="Simple Strumming Patterns",
        video_url="https://youtube.com/watch?v=example3",
        order=2
    )

    lesson4 = Lesson(
        offer_id=offer3.id,
        title="Putting It All Together",
        video_url="https://youtube.com/watch?v=example4",
        order=3
    )

    db.session.add_all([
        lesson1, lesson2, lesson3, lesson4
    ])

    # ============================================================
    # REQUESTS
    # ============================================================

    req1 = Request(
        student_id=sam.id,
        skill_id=chess.id,
        description="I'd like to learn a few reliable chess openings and understand when to use them.",
        preferred_time="Weekday afternoons"
    )

    req2 = Request(
        student_id=alex.id,
        skill_id=study_skills.id,
        description="Looking for advice on planning revision before multiple exams.",
        preferred_time="After school"
    )

    req3 = Request(
        student_id=maya.id,
        skill_id=python.id,
        description="I'd like to learn enough Python to build a small project.",
        preferred_time="Saturday mornings"
    )

    req4 = Request(
        student_id=daniel.id,
        skill_id=public_speaking.id,
        description="Want to become more confident when presenting in class.",
        preferred_time="Tuesday or Thursday"
    )

    req5 = Request(
        student_id=sara.id,
        skill_id=photography.id,
        description="Looking for someone who can teach basic phone photography and composition.",
        preferred_time="Weekend"
    )

    db.session.add_all([
        req1, req2, req3, req4, req5
    ])
    db.session.flush()

    # ============================================================
    # REQUEST UPVOTES
    # ============================================================

    db.session.add_all([
        RequestUpvote(request_id=req1.id, user_id=john.id),
        RequestUpvote(request_id=req1.id, user_id=priya.id),
        RequestUpvote(request_id=req1.id, user_id=maya.id),

        RequestUpvote(request_id=req2.id, user_id=sara.id),
        RequestUpvote(request_id=req2.id, user_id=priya.id),

        RequestUpvote(request_id=req3.id, user_id=daniel.id),
        RequestUpvote(request_id=req3.id, user_id=john.id),

        RequestUpvote(request_id=req4.id, user_id=sara.id),

        RequestUpvote(request_id=req5.id, user_id=maya.id),
        RequestUpvote(request_id=req5.id, user_id=alex.id),
    ])

    # ============================================================
    # UPCOMING SESSIONS
    # ============================================================

    upcoming1 = Session(
        offer_id=offer1.id,
        start_time=now + timedelta(days=2, hours=3),
        end_time=now + timedelta(days=2, hours=4),
        meeting_link="https://zoom.us/j/example123"
    )

    upcoming2 = Session(
        offer_id=offer4.id,
        start_time=now + timedelta(days=4, hours=2),
        end_time=now + timedelta(days=4, hours=3),
        meeting_link="https://zoom.us/j/python101"
    )

    upcoming3 = Session(
        offer_id=offer5.id,
        start_time=now + timedelta(days=5, hours=1),
        end_time=now + timedelta(days=5, hours=2),
        meeting_link="https://zoom.us/j/speaking101"
    )

    upcoming4 = Session(
        offer_id=offer6.id,
        start_time=now + timedelta(days=7),
        end_time=now + timedelta(days=7, hours=1),
        meeting_link="https://zoom.us/j/photo101"
    )

    db.session.add_all([
        upcoming1,
        upcoming2,
        upcoming3,
        upcoming4
    ])
    db.session.flush()

    # Upcoming enrollments
    db.session.add_all([
        Enrollment(
            session_id=upcoming1.id,
            student_id=priya.id,
            status="confirmed"
        ),
        Enrollment(
            session_id=upcoming1.id,
            student_id=sam.id,
            status="confirmed"
        ),
        Enrollment(
            session_id=upcoming2.id,
            student_id=maya.id,
            status="confirmed"
        ),
        Enrollment(
            session_id=upcoming2.id,
            student_id=sara.id,
            status="confirmed"
        ),
        Enrollment(
            session_id=upcoming3.id,
            student_id=alex.id,
            status="confirmed"
        ),
        Enrollment(
            session_id=upcoming4.id,
            student_id=sam.id,
            status="confirmed"
        ),
    ])

    # ============================================================
    # PAST COMPLETED SESSION WITH RECORDING
    # ============================================================

    past1 = Session(
        offer_id=offer1.id,
        start_time=now - timedelta(days=10, hours=2),
        end_time=now - timedelta(days=10, hours=1),
        meeting_link="https://zoom.us/j/pastcubing",
        recording_url="https://youtube.com/watch?v=cubing-recording"
    )

    db.session.add(past1)
    db.session.flush()

    db.session.add_all([
        Enrollment(
            session_id=past1.id,
            student_id=sam.id,
            status="confirmed",
            attended=True
        ),
        Enrollment(
            session_id=past1.id,
            student_id=priya.id,
            status="confirmed",
            attended=True
        ),
        Enrollment(
            session_id=past1.id,
            student_id=maya.id,
            status="confirmed",
            attended=True
        ),
    ])

    db.session.flush()

    db.session.add_all([
        Feedback(
            session_id=past1.id,
            student_id=sam.id,
            rating=5,
            comment="Really clear explanation. I finally understand the beginner method!"
        ),
        Feedback(
            session_id=past1.id,
            student_id=priya.id,
            rating=5,
            comment="Very easy to follow and genuinely fun."
        ),
        Feedback(
            session_id=past1.id,
            student_id=maya.id,
            rating=4,
            comment="Great session. Would definitely recommend it to beginners."
        ),
    ])

    # ============================================================
    # PAST SESSION - RECORDING OVERDUE
    # ============================================================

    past2 = Session(
        offer_id=offer2.id,
        start_time=now - timedelta(days=4, hours=2),
        end_time=now - timedelta(days=4, hours=1),
        meeting_link="https://zoom.us/j/calculus-review",
        recording_url=None
    )

    db.session.add(past2)
    db.session.flush()

    db.session.add_all([
        Enrollment(
            session_id=past2.id,
            student_id=sam.id,
            status="confirmed",
            attended=True
        ),
        Enrollment(
            session_id=past2.id,
            student_id=alex.id,
            status="confirmed",
            attended=True
        ),
        Enrollment(
            session_id=past2.id,
            student_id=john.id,
            status="confirmed",
            attended=False
        ),
    ])

    db.session.flush()

    db.session.add_all([
        Feedback(
            session_id=past2.id,
            student_id=sam.id,
            rating=5,
            comment="The examples made the harder topics much easier."
        ),
        Feedback(
            session_id=past2.id,
            student_id=alex.id,
            rating=4,
            comment="Helpful review before the test."
        ),
    ])

    # ============================================================
    # RECENT SESSION - FEEDBACK PENDING
    # ============================================================

    past3 = Session(
        offer_id=offer4.id,
        start_time=now - timedelta(days=1, hours=2),
        end_time=now - timedelta(days=1, hours=1),
        meeting_link="https://zoom.us/j/python-basics",
        recording_url="https://youtube.com/watch?v=python-recording"
    )

    db.session.add(past3)
    db.session.flush()

    db.session.add_all([
        Enrollment(
            session_id=past3.id,
            student_id=maya.id,
            status="confirmed",
            attended=True
        ),
        Enrollment(
            session_id=past3.id,
            student_id=sara.id,
            status="confirmed",
            attended=True
        ),
    ])

    db.session.flush()

    # Maya has submitted feedback; Sara has not.
    db.session.add(
        Feedback(
            session_id=past3.id,
            student_id=maya.id,
            rating=5,
            comment="The exercises were much better than just watching a tutorial."
        )
    )

    # ============================================================
    # CANCELLED SESSION
    # ============================================================

    cancelled = Session(
        offer_id=offer7.id,
        start_time=now - timedelta(days=2),
        end_time=now - timedelta(days=2) + timedelta(hours=1),
        meeting_link="https://zoom.us/j/cancelled-debate",
        status="cancelled",
        cancelled_reason="Teacher was unavailable due to a school event."
    )

    db.session.add(cancelled)
    db.session.flush()

    db.session.add(
        Enrollment(
            session_id=cancelled.id,
            student_id=alex.id,
            status="confirmed"
        )
    )

    # ============================================================
    # WAITLISTED STUDENT
    # ============================================================

    db.session.add(
        Enrollment(
            session_id=upcoming3.id,
            student_id=daniel.id,
            status="waitlisted"
        )
    )

    # ============================================================
    # COMMENTS
    # ============================================================

    db.session.add_all([
        Comment(
            offer_id=offer1.id,
            user_id=sam.id,
            content="Would this be suitable for someone who has never solved a cube before?"
        ),
        Comment(
            offer_id=offer1.id,
            user_id=john.id,
            content="Absolutely! We start from the basics."
        ),
        Comment(
            offer_id=offer4.id,
            user_id=maya.id,
            content="Do I need any previous programming experience?"
        ),
        Comment(
            offer_id=offer4.id,
            user_id=daniel.id,
            content="Nope! This is designed for complete beginners."
        ),
        Comment(
            offer_id=offer5.id,
            user_id=alex.id,
            content="Will there be opportunities to practise during the session?"
        ),
        Comment(
            offer_id=offer5.id,
            user_id=sara.id,
            content="Yes, there will be short speaking exercises."
        ),
    ])

    # ============================================================
    # COMMIT
    # ============================================================

    db.session.commit()

    print("\nDatabase seeded successfully!")
    print("\nTest accounts (all passwords: password123):")
    print("  john@school.edu        - Rubik's Cube teacher")
    print("  priya@school.edu       - Calculus + Guitar teacher")
    print("  sam@school.edu         - Learner + chess requester")
    print("  alex@school.edu        - Learner + Graphic Design teacher")
    print("  maya@school.edu        - Photography teacher + Python learner")
    print("  daniel@school.edu      - Python teacher")
    print("  sara@school.edu        - Public Speaking + Debate teacher")
    print("  incomplete@school.edu  - INCOMPLETE PROFILE (profile-gate testing)")

    print("\nSeeded:")
    print("  - 8 users")
    print("  - 10 skills")
    print("  - 8 offers")
    print("  - 5 requests")
    print("  - Multiple upcoming sessions")
    print("  - Completed sessions")
    print("  - Recorded session")
    print("  - Overdue recording")
    print("  - Pending feedback")
    print("  - Cancelled session")
    print("  - Confirmed + waitlisted enrollments")
    print("  - Request upvotes")
    print("  - Offer comments")