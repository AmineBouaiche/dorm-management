from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record_event(
    db: Session,
    *,
    actor_user_id: int,
    action: str,
    resource_type: str,
    resource_id: int,
    request_id: str,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    event = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        request_id=request_id,
        details=details,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events(db: Session, *, offset: int = 0, limit: int = 100) -> list[AuditLog]:
    statement = (
        select(AuditLog)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def count_events(db: Session) -> int:
    return int(db.scalar(select(func.count(AuditLog.id))) or 0)
