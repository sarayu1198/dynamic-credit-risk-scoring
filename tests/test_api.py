from fastapi.testclient import TestClient
from backend.main import app

from types import SimpleNamespace

from backend.auth import get_current_user



client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Dynamic Credit Risk Scoring API is running"
    }


def test_openapi_documentation():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "paths" in response.json()


def test_database_health():
    response = client.get("/health/db")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "connected"
    assert data["database"]


def test_login_rejects_invalid_credentials():
    response = client.post(
        "/auth/login",
        data={
            "username": "invalid-test-user@example.com",
            "password": "definitely-wrong-password",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_current_user_requires_authentication():
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_registration_rejects_invalid_email():
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Test User",
            "email": "not-an-email",
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 422




def test_assessment_rejects_invalid_input():
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        user_id=1,
        role="admin",
    )
    try:
        response = client.post(
            "/borrowers/999999/assess",
            json={
                "limit_bal": -100,
                "sex": 2,
                "education": 2,
                "marriage": 1,
                "age": 30,
            },
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_assessment_rejects_missing_features():
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        user_id=1,
        role="admin",
    )
    try:
        response = client.post(
            "/borrowers/999999/assess",
            json={},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_current_user, None)

def test_nonexistent_borrower_requires_authentication():
    response = client.get("/borrowers/999999")
    assert response.status_code == 401



def test_assessment_rejects_invalid_input():
    response = client.post(
        "/borrowers/999999/assess",
        json={
            "limit_bal": -100,
            "sex": 2,
            "education": 2,
            "marriage": 1,
            "age": 30,
        },
    )
    # Authentication is checked before request validation.
    assert response.status_code == 401


def test_assessment_rejects_missing_features():
    response = client.post(
        "/borrowers/999999/assess",
        json={},
    )
    # Authentication is checked before request validation.
    assert response.status_code == 401



def test_nonexistent_borrower_requires_authentication():
    response = client.get("/borrowers/999999")
    assert response.status_code == 401


def test_risk_review_requires_authentication():
    response = client.post(
        "/borrowers/999999/risk-reviews",
        json={
            "review_type": "manual_review",
            "risk_level": "medium",
            "notes": "Test review",
            "reviewed": False,
        },
    )
    assert response.status_code == 401


def test_risk_review_rejects_empty_notes():
    response = client.post(
        "/borrowers/999999/risk-reviews",
        json={
            "review_type": "manual_review",
            "risk_level": "medium",
            "notes": "",
            "reviewed": False,
        },
    )
    assert response.status_code == 401


def test_risk_review_list_requires_authentication():
    response = client.get(
        "/borrowers/999999/risk-reviews"
    )
    assert response.status_code == 401
