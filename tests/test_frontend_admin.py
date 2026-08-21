from pathlib import Path

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
FRONTEND = Path(__file__).resolve().parents[1] / "frontend"


def test_admin_frontend_routes_exist():
    for path in ["/admin", "/admin/rooms", "/admin/residences", "/admin/students", "/admin/students/1", "/admin/bookings", "/admin/bookings/1"]:
        response = client.get(path)
        assert response.status_code == 200
        assert "Residence" in response.text


def test_admin_navigation_and_pages_are_operational():
    navigation = (FRONTEND / "js/components/navigation.js").read_text(encoding="utf-8")
    assert "Overview" in navigation and "Students" in navigation and "Bookings" in navigation
    overview = (FRONTEND / "admin/overview.html").read_text(encoding="utf-8")
    assert "Confirmed revenue" not in overview  # rendered from API, not hard-coded fake data
    assert "data-admin-metrics" in overview


def test_admin_api_client_uses_real_backend_endpoints():
    source = (FRONTEND / "js/api/client.js").read_text(encoding="utf-8")
    for endpoint in ["/admin/analytics", "/admin/students", "/admin/bookings", "/admin/buildings", "/admin/rooms"]:
        assert endpoint in source
    assert "confirmAdminBooking" in source
    assert "cancelAdminBooking" in source


def test_admin_inventory_supports_updates_without_delete():
    rooms = (FRONTEND / "js/pages/admin/rooms.js").read_text(encoding="utf-8")
    residences = (FRONTEND / "js/pages/admin/residences.js").read_text(encoding="utf-8")
    assert "updateRoom" in rooms and "is_active" in rooms
    assert "updateBuilding" in residences and "is_active" in residences
    assert "DELETE" not in rooms and "DELETE" not in residences


def test_admin_role_now_redirects_to_real_overview():
    config = (FRONTEND / "js/config.js").read_text(encoding="utf-8")
    assert 'adminHome: "/admin"' in config
