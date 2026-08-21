from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"


def test_rooms_pages_are_served() -> None:
    client = TestClient(app)
    assert client.get("/rooms").status_code == 200
    assert client.get("/rooms/1").status_code == 200
    assert client.get("/booking/confirm").status_code == 200


def test_room_catalogue_contains_locked_filters() -> None:
    html = (FRONTEND / "rooms" / "index.html").read_text(encoding="utf-8")
    for field in ('name="start_date"', 'name="end_date"', 'name="room_type"', 'name="building_id"'):
        assert field in html


def test_room_detail_does_not_submit_booking() -> None:
    js = (FRONTEND / "js" / "pages" / "room-detail.js").read_text(encoding="utf-8")
    assert 'action.href = `/booking/confirm?${next}`' in js
    assert 'method: "POST"' not in js


def test_representative_residence_assets_exist() -> None:
    assets = FRONTEND / "assets" / "residences"
    for name in ("north-hall.svg", "west-court.svg", "riverside-house.svg", "clifton-lodge.svg"):
        assert (assets / name).exists()
