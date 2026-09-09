import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app
from models import db, User


@pytest.fixture
def client():
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
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