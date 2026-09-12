import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app
from models import (
    db,
    User,
    Skill,
    Offer,
    Session,
    Enrollment,
    Request,
    RequestUpvote,
    Feedback,
    Lesson,
    Comment
)



@pytest.fixture
def client():
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        RATELIMIT_ENABLED=False,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SECRET_KEY="test-secret-key"
    )

    with app.app_context():
        db.create_all()

        yield app.test_client()

        db.session.remove()
        db.drop_all()


def test_homepage(client):
    response = client.get("/")

    assert response.status_code == 200


def test_404_page(client):
    response = client.get("/this-page-does-not-exist")

    assert response.status_code == 404


def test_signup(client):
    response = client.post(
        "/add-user",
        data={
            "name": "Test Student",
            "email": "test@example.com",
            "password": "TestPassword123"
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    user = User.query.filter_by(email="test@example.com").first()

    assert user is not None
    assert user.name == "Test Student"


def test_login(client):
    client.post(
        "/add-user",
        data={
            "name": "Test Student",
            "email": "test@example.com",
            "password": "TestPassword123"
        }
    )

    response = client.post(
        "/login",
        data={
            "email": "test@example.com",
            "password": "TestPassword123"
        },
        follow_redirects=True
    )

    assert response.status_code == 200


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")

    assert response.status_code == 302


def test_signup_rejects_invalid_email(client):
    response = client.post(
        "/add-user",
        data={
            "name": "Test Student",
            "email": "not-an-email",
            "password": "TestPassword123"
        }
    )

    assert response.status_code == 302

    user = User.query.filter_by(email="not-an-email").first()

    assert user is None

def test_duplicate_enrollment_rejected(client):
    user = User(
        name="Student",
        email="student@example.com"
    )
    user.set_password("TestPassword123")

    teacher = User(
        name="Teacher",
        email="teacher@example.com"
    )
    teacher.set_password("TestPassword123")

    skill = Skill(
        name="Python",
        category="Technology"
    )

    db.session.add_all([user, teacher, skill])
    db.session.commit()

    offer = Offer(
        teacher_id=teacher.id,
        skill_id=skill.id,
        title="Learn Python",
        level="Beginner"
    )

    db.session.add(offer)
    db.session.commit()

    session = Session(
        offer_id=offer.id,
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(hours=1)
    )

    db.session.add(session)
    db.session.commit()

    enrollment1 = Enrollment(
        session_id=session.id,
        student_id=user.id
    )

    db.session.add(enrollment1)
    db.session.commit()

    enrollment2 = Enrollment(
        session_id=session.id,
        student_id=user.id
    )

    db.session.add(enrollment2)

    with pytest.raises(Exception):
        db.session.commit()

    db.session.rollback()


def _create_user(name, email):
    user = User(name=name, email=email)
    user.set_password("TestPassword123")
    db.session.add(user)
    db.session.flush()
    return user


def _create_offer(teacher, title="Test Offer"):
    skill = Skill(name=f"Skill {title}", category="Academic")
    db.session.add(skill)
    db.session.flush()
    offer = Offer(
        teacher_id=teacher.id,
        skill_id=skill.id,
        title=title,
        level="Beginner",
    )
    db.session.add(offer)
    db.session.commit()
    return offer, skill


def _login(client, email):
    user = User.query.filter_by(email=email).one()
    with client.session_transaction() as session:
        session["_user_id"] = str(user.id)
        session["_fresh"] = True


def test_offer_owner_can_delete_offer_without_sessions(client):
    teacher = _create_user("Teacher", "teacher@example.com")
    offer, _ = _create_offer(teacher)
    offer_id = offer.id
    _login(client, teacher.email)

    response = client.post(f"/offers/{offer_id}/delete")

    assert response.status_code == 302
    assert db.session.get(Offer, offer_id) is None


def test_other_user_cannot_delete_offer(client):
    teacher = _create_user("Teacher", "teacher@example.com")
    other = _create_user("Other", "other@example.com")
    offer, _ = _create_offer(teacher)
    _login(client, other.email)

    response = client.post(f"/offers/{offer.id}/delete")

    assert response.status_code == 403
    assert db.session.get(Offer, offer.id) is not None


def test_offer_with_session_cannot_be_deleted(client):
    teacher = _create_user("Teacher", "teacher@example.com")
    offer, _ = _create_offer(teacher)
    session = Session(
        offer_id=offer.id,
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(hours=1),
    )
    db.session.add(session)
    db.session.commit()
    _login(client, teacher.email)

    response = client.post(f"/offers/{offer.id}/delete")

    assert response.status_code == 302
    assert db.session.get(Offer, offer.id) is not None
    assert db.session.get(Session, session.id) is not None


def test_deleting_offer_removes_lessons_comments_but_not_teacher(client):
    teacher = _create_user("Teacher", "teacher@example.com")
    offer, _ = _create_offer(teacher)
    lesson = Lesson(
        offer_id=offer.id,
        title="Part One",
        video_url="https://example.com/video",
    )
    comment = Comment(
        offer_id=offer.id,
        user_id=teacher.id,
        content="Useful note",
    )
    db.session.add_all([lesson, comment])
    db.session.commit()
    lesson_id, comment_id, teacher_id = lesson.id, comment.id, teacher.id
    offer_id = offer.id
    _login(client, teacher.email)

    response = client.post(f"/offers/{offer_id}/delete")

    assert response.status_code == 302
    assert db.session.get(Offer, offer_id) is None
    assert db.session.get(Lesson, lesson_id) is None
    assert db.session.get(Comment, comment_id) is None
    assert db.session.get(User, teacher_id) is not None


def test_request_owner_can_delete_request_and_upvotes_but_not_skill(client):
    owner = _create_user("Owner", "owner@example.com")
    voter = _create_user("Voter", "voter@example.com")
    skill = Skill(name="Shared Skill", category="Academic")
    db.session.add(skill)
    db.session.flush()
    learning_request = Request(
        student_id=owner.id,
        skill_id=skill.id,
        description="Learn this",
    )
    db.session.add(learning_request)
    db.session.flush()
    upvote = RequestUpvote(request_id=learning_request.id, user_id=voter.id)
    db.session.add(upvote)
    db.session.commit()
    request_id, upvote_id, skill_id = learning_request.id, upvote.id, skill.id
    _login(client, owner.email)

    response = client.post(f"/requests/{request_id}/delete")

    assert response.status_code == 302
    assert db.session.get(Request, request_id) is None
    assert db.session.get(RequestUpvote, upvote_id) is None
    assert db.session.get(Skill, skill_id) is not None


def test_other_user_cannot_delete_request(client):
    owner = _create_user("Owner", "owner@example.com")
    other = _create_user("Other", "other@example.com")
    skill = Skill(name="Request Skill", category="Academic")
    db.session.add(skill)
    db.session.flush()
    request_record = Request(
        student_id=owner.id,
        skill_id=skill.id,
        description="Learn this",
    )
    db.session.add(request_record)
    db.session.commit()
    _login(client, other.email)

    response = client.post(f"/requests/{request_record.id}/delete")

    assert response.status_code == 403
    assert db.session.get(Request, request_record.id) is not None


def test_comment_author_can_delete_comment_only(client):
    author = _create_user("Author", "author@example.com")
    offer, _ = _create_offer(author)
    comment = Comment(offer_id=offer.id, user_id=author.id, content="Delete me")
    db.session.add(comment)
    db.session.commit()
    comment_id, offer_id, author_id = comment.id, offer.id, author.id
    _login(client, author.email)

    response = client.post(f"/comments/{comment_id}/delete")

    assert response.status_code == 302
    assert db.session.get(Comment, comment_id) is None
    assert db.session.get(Offer, offer_id) is not None
    assert db.session.get(User, author_id) is not None


def test_other_user_cannot_delete_comment(client):
    author = _create_user("Author", "author@example.com")
    other = _create_user("Other", "other@example.com")
    offer, _ = _create_offer(author)
    comment = Comment(offer_id=offer.id, user_id=author.id, content="Keep me")
    db.session.add(comment)
    db.session.commit()
    _login(client, other.email)

    response = client.post(f"/comments/{comment.id}/delete")

    assert response.status_code == 403
    assert db.session.get(Comment, comment.id) is not None


def test_offer_teacher_can_delete_lesson_only(client):
    teacher = _create_user("Teacher", "teacher@example.com")
    offer, _ = _create_offer(teacher)
    lesson = Lesson(
        offer_id=offer.id,
        title="Part One",
        video_url="https://example.com/video",
    )
    db.session.add(lesson)
    db.session.commit()
    lesson_id, offer_id = lesson.id, offer.id
    _login(client, teacher.email)

    response = client.post(f"/lessons/{lesson_id}/delete")

    assert response.status_code == 302
    assert db.session.get(Lesson, lesson_id) is None
    assert db.session.get(Offer, offer_id) is not None


def test_other_user_cannot_delete_lesson(client):
    teacher = _create_user("Teacher", "teacher@example.com")
    other = _create_user("Other", "other@example.com")
    offer, _ = _create_offer(teacher)
    lesson = Lesson(
        offer_id=offer.id,
        title="Part One",
        video_url="https://example.com/video",
    )
    db.session.add(lesson)
    db.session.commit()
    _login(client, other.email)

    response = client.post(f"/lessons/{lesson.id}/delete")

    assert response.status_code == 403
    assert db.session.get(Lesson, lesson.id) is not None


@pytest.mark.parametrize("path", [
    "/offers/1/delete",
    "/requests/1/delete",
    "/comments/1/delete",
    "/lessons/1/delete",
])
def test_get_delete_routes_do_not_delete(client, path):
    response = client.get(path)

    assert response.status_code == 405


@pytest.mark.parametrize("path", [
    "/offers/1/delete",
    "/requests/1/delete",
    "/comments/1/delete",
    "/lessons/1/delete",
])
def test_unauthenticated_delete_routes_require_login(client, path):
    response = client.post(path)

    assert response.status_code == 302


def test_delete_routes_require_csrf_when_enabled(client):
    teacher = _create_user("Teacher", "teacher@example.com")
    offer, _ = _create_offer(teacher)
    app.config["WTF_CSRF_ENABLED"] = True
    with client.session_transaction() as session:
        session["_user_id"] = str(teacher.id)
        session["_fresh"] = True

    response = client.post(f"/offers/{offer.id}/delete")

    assert response.status_code == 400
    assert db.session.get(Offer, offer.id) is not None

    def test_duplicate_upvote_rejected(client):
        user = User(
            name="Student",
            email="student@example.com"
        )
        user.set_password("TestPassword123")

        skill = Skill(
            name="Python",
            category="Technology"
        )

        db.session.add_all([user, skill])
        db.session.commit()

        request = Request(
            student_id=user.id,
            skill_id=skill.id,
            description="I want to learn Python"
        )

        db.session.add(request)
        db.session.commit()

        upvote1 = RequestUpvote(
            request_id=request.id,
            user_id=user.id
        )

        db.session.add(upvote1)
        db.session.commit()

        upvote2 = RequestUpvote(
            request_id=request.id,
            user_id=user.id
        )

        db.session.add(upvote2)

        with pytest.raises(Exception):
            db.session.commit()

        db.session.rollback()
