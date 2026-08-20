from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.building import BuildingCreate, BuildingRead, BuildingUpdate
from app.services import building_service

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get("", response_model=list[BuildingRead])
def list_buildings(db: Session = Depends(get_db)) -> list[BuildingRead]:
    return building_service.list_buildings(db, active_only=True)


@router.post("", response_model=BuildingRead, status_code=status.HTTP_201_CREATED)
def create_building(
    data: BuildingCreate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> BuildingRead:
    try:
        return building_service.create_building(db, data)
    except building_service.BuildingAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Building name already exists") from exc


@router.patch("/{building_id}", response_model=BuildingRead)
def update_building(
    building_id: int,
    data: BuildingUpdate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> BuildingRead:
    try:
        return building_service.update_building(db, building_id, data)
    except building_service.BuildingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found") from exc
    except building_service.BuildingAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Building name already exists") from exc
