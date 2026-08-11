import pytest

from src.app import activities


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities_with_expected_shape(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert "cache-control" in response.headers
    assert "no-store" in response.headers["cache-control"]

    payload = response.json()
    assert isinstance(payload, dict)
    assert len(payload) == len(activities)

    chess = payload["Chess Club"]
    assert set(chess.keys()) == {"description", "schedule", "max_participants", "participants"}
    assert isinstance(chess["participants"], list)


def test_signup_adds_participant(client):
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"

    activities_response = client.get("/activities")
    participants = activities_response.json()[activity_name]["participants"]
    assert email in participants


def test_signup_duplicate_participant_returns_400(client):
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup", params={"email": existing_email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_unknown_activity_returns_404(client):
    response = client.post("/activities/Unknown Activity/signup", params={"email": "user@mergington.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_missing_email_returns_422(client):
    response = client.post("/activities/Chess Club/signup")

    assert response.status_code == 422


def test_unregister_removes_participant(client):
    activity_name = "Chess Club"
    email = "daniel@mergington.edu"

    response = client.delete(f"/activities/{activity_name}/participants", params={"email": email})

    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"

    activities_response = client.get("/activities")
    participants = activities_response.json()[activity_name]["participants"]
    assert email not in participants


def test_unregister_unknown_activity_returns_404(client):
    response = client.delete("/activities/Unknown Activity/participants", params={"email": "user@mergington.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_not_enrolled_returns_404(client):
    response = client.delete("/activities/Chess Club/participants", params={"email": "not_enrolled@mergington.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_missing_email_returns_422(client):
    response = client.delete("/activities/Chess Club/participants")

    assert response.status_code == 422


@pytest.mark.xfail(reason="Capacity guard is not implemented yet.", strict=False)
def test_signup_rejects_when_activity_is_at_capacity(client):
    activity_name = "Chess Club"
    max_participants = activities[activity_name]["max_participants"]
    activities[activity_name]["participants"] = [f"student{i}@mergington.edu" for i in range(max_participants)]

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "overflow@mergington.edu"},
    )

    assert response.status_code in (400, 409)


@pytest.mark.xfail(reason="Email format/blank validation is not implemented yet.", strict=False)
@pytest.mark.parametrize("email", ["", "invalid-email", "   "])
def test_signup_rejects_invalid_or_blank_email(client, email):
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code in (400, 422)
