from decimal import Decimal

from sqlalchemy import select

from app.db.database import SessionLocal
from app.models.building import Building
from app.models.enums import RoomType
from app.models.room import Room

RESIDENCES = [
    ("North Hall", "14 University Avenue", "/static/assets/residences/north-hall.svg", "A", {RoomType.SHARED: 155, RoomType.SINGLE: 185, RoomType.STUDIO: 225}),
    ("West Court", "8 College Road", "/static/assets/residences/west-court.svg", "B", {RoomType.SHARED: 150, RoomType.SINGLE: 180, RoomType.STUDIO: 215}),
    ("Riverside House", "22 Riverside Walk", "/static/assets/residences/riverside-house.svg", "C", {RoomType.SHARED: 160, RoomType.SINGLE: 195, RoomType.STUDIO: 235}),
    ("Clifton Lodge", "31 Clifton Terrace", "/static/assets/residences/clifton-lodge.svg", "D", {RoomType.SHARED: 145, RoomType.SINGLE: 175, RoomType.STUDIO: 210}),
]
ROOM_PLAN = [(101, RoomType.SINGLE, 1), (102, RoomType.SINGLE, 1), (103, RoomType.SHARED, 2), (104, RoomType.SHARED, 2), (201, RoomType.SINGLE, 1), (202, RoomType.STUDIO, 1), (203, RoomType.SINGLE, 1), (204, RoomType.STUDIO, 1)]


def main() -> None:
    db = SessionLocal()
    try:
        for name, address, image_url, prefix, rates in RESIDENCES:
            building = db.scalar(select(Building).where(Building.name == name))
            if building is None:
                building = Building(name=name, address=address, image_url=image_url, is_active=True)
                db.add(building)
                db.flush()
            else:
                building.address = address
                building.image_url = image_url
                building.is_active = True
            for number, room_type, capacity in ROOM_PLAN:
                room_number = f"{prefix}{number}"
                room = db.scalar(select(Room).where(Room.building_id == building.id, Room.room_number == room_number))
                if room is None:
                    db.add(Room(building_id=building.id, room_number=room_number, room_type=room_type, capacity=capacity, weekly_rate=Decimal(str(rates[room_type])), is_active=True))
        db.commit()
        print("Demo accommodation data is ready.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
