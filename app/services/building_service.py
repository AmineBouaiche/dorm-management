from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.building import Building
from app.schemas.building import BuildingCreate, BuildingUpdate


class BuildingNotFoundError(Exception):
    pass


class BuildingAlreadyExistsError(Exception):
    pass


def list_buildings(
    db: Session, *, active_only: bool = True, offset: int = 0, limit: int = 100
) -> list[Building]:
    statement = select(Building)
    if active_only:
        statement = statement.where(Building.is_active.is_(True))
    statement = (
        statement.order_by(Building.name, Building.id).offset(offset).limit(limit)
    )
    return list(db.scalars(statement).all())



def count_buildings(db: Session, *, active_only: bool = True) -> int:
    statement = select(func.count(Building.id))
    if active_only:
        statement = statement.where(Building.is_active.is_(True))
    return int(db.scalar(statement) or 0)


def get_building(db: Session, building_id: int) -> Building:
    building = db.get(Building, building_id)
    if building is None:
        raise BuildingNotFoundError
    return building


def create_building(db: Session, data: BuildingCreate) -> Building:
    building = Building(
        name=data.name.strip(),
        address=data.address.strip(),
        image_url=data.image_url.strip() if data.image_url else None,
        is_active=True,
    )
    db.add(building)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise BuildingAlreadyExistsError from exc

    db.refresh(building)
    return building


def update_building(db: Session, building_id: int, data: BuildingUpdate) -> Building:
    building = get_building(db, building_id)
    changes = data.model_dump(exclude_unset=True)

    if "name" in changes:
        changes["name"] = changes["name"].strip()
    if "address" in changes:
        changes["address"] = changes["address"].strip()
    if "image_url" in changes and changes["image_url"] is not None:
        changes["image_url"] = changes["image_url"].strip() or None

    for field, value in changes.items():
        setattr(building, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise BuildingAlreadyExistsError from exc

    db.refresh(building)
    return building
