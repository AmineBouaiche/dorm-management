from fastapi.testclient import TestClient

from tests.helpers import bearer, register_and_login_student


def test_student_can_read_own_profile(client: TestClient) -> None:
    student, token = register_and_login_student(client, "41001")
    response = client.get("/api/students/me", headers=bearer(token))
    assert response.status_code == 200
    assert response.json()["student_id"] == student["student_id"]


def test_student_profile_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/students/me").status_code == 401
