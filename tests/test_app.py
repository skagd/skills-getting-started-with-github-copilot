import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities as app_activities


@pytest.fixture
def client():
    """Create a client and reset app state before each test."""
    original_activities = copy.deepcopy(app_activities)
    app_activities.clear()
    app_activities.update(copy.deepcopy(original_activities))

    with TestClient(app) as test_client:
        yield test_client

    app_activities.clear()
    app_activities.update(copy.deepcopy(original_activities))


def test_root_redirects_to_static_index():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["description"]
    assert payload["Chess Club"]["participants"]


def test_signup_for_activity_adds_email():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in app_activities[activity_name]["participants"]


def test_duplicate_signup_returns_error():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    original_count = len(app_activities[activity_name]["participants"])

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert len(app_activities[activity_name]["participants"]) == original_count


def test_unregister_for_activity_removes_email():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    assert email not in app_activities[activity_name]["participants"]


def test_unregister_missing_student_returns_error():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    email = "missing@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unknown_activity_returns_404():
    # Arrange
    client = TestClient(app)
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
